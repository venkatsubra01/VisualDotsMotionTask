import json
import os
import random
from flask import Flask, request, jsonify, render_template, send_file
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend to prevent threading issues
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Constants
# Constants
RESULTS_FILE = "results.json"

# Magnitude of the coherence bounds (internally will pick
# left or right randomly)
COHERENCE_LOWER_BOUND = 0
COHERENCE_UPPER_BOUND = 0.5
PLOT_FILE = "static/results_plot.png"
NUM_ENTRIES_NEEDED_TO_COUNT = 30

app = Flask(__name__)

# Ensure static directory exists
if not os.path.exists("static"):
    os.mkdir("static")

# Used to add a new trial result to the JSON file
def save_result(trial_result):
    if os.path.exists(RESULTS_FILE):
        # Get the existing results
        with open(RESULTS_FILE, "r") as file:
            try:
                results = json.load(file)
            except json.JSONDecodeError:
                results = []
    else:
        results = []
    # Append to existing results
    results.append(trial_result)
    # Save the updated results
    with open(RESULTS_FILE, "w") as file:
        json.dump(results, file, indent=4)

# Used to load the results from the JSON file
def load_results():
    """ Load results from JSON file """
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

# Generate desired plots
def generate_plot():
    results = load_results()
    if not results:
        return  # No data to plot

    df = pd.DataFrame(results)
    df['choice_right'] = df['user'] == 'right'

    num_bins = 10  # Adjust based on data density
    df['coherence_bin'] = pd.cut(
        df['coherence'],
        bins=np.linspace(-COHERENCE_UPPER_BOUND, COHERENCE_UPPER_BOUND, num_bins + 1),
        labels=False,
        include_lowest=True
    )

    bin_means = df.groupby('coherence_bin')['coherence'].mean()
    prob_right = df.groupby('coherence_bin')['choice_right'].mean()

    # --- P(Choosing Right) vs. Coherence ---
    plt.figure(figsize=(6, 4))
    plt.plot(bin_means, prob_right, marker='o', linestyle='-', label="P(choose right)")
    plt.xlabel("Coherence Value")
    plt.ylabel("P(Choose Right)")
    plt.title("P(Choosing Right) vs. Coherence")
    plt.ylim(0, 1.2)
    plt.xlim(-COHERENCE_UPPER_BOUND, COHERENCE_UPPER_BOUND)
    plt.axhline(0.5, linestyle="--", color="gray", alpha=0.6)
    plt.axvline(0, linestyle="--", color="gray", alpha=0.6)
    plt.grid()
    plt.savefig("static/prob_choose_right.png")
    plt.close()

    # --- Reaction Time vs. Coherence ---
    trials = list(range(1, len(results) + 1))
    coherence = [r["coherence"] for r in results]
    reaction_times = [r["reaction_time"] for r in results]
    correct_guesses = [r["correct_guess"] for r in results]
    colors = ["green" if correct else "red" for correct in correct_guesses]

    plt.figure(figsize=(6, 4))
    plt.scatter(coherence, reaction_times, c=colors, edgecolors="black")
    plt.xlabel("Coherence")
    plt.ylabel("Reaction Times (ms)")
    plt.title("Reaction Time vs Coherence")
    plt.ylim(0, 2200)
    plt.xlim(-COHERENCE_UPPER_BOUND, COHERENCE_UPPER_BOUND)
    plt.grid(True)
    plt.savefig("static/reaction_time_vs_coherence.png")
    plt.close()

    # --- Probability Correct vs. Coherence ---
    percentage_correct = df.groupby('coherence_bin')['correct_guess'].mean()

    plt.figure(figsize=(6, 4))
    plt.plot(bin_means, percentage_correct, marker='o', linestyle='-')
    plt.xlabel("Coherence Bin")
    plt.ylabel("Probability Correct")
    plt.title("Probability Correct vs Coherence")
    plt.ylim(0, 1.2)
    plt.xlim(-COHERENCE_UPPER_BOUND, COHERENCE_UPPER_BOUND)
    plt.grid(True)
    plt.savefig("static/probability_correct.png")
    plt.close()
def get_curr_leader():
    results = load_results()
    if not results:
        return  # No data to plot
    df = pd.DataFrame(results)
    # Get the number of entries for each person
    counts_by_name = df.groupby('name').size()

    # Get the indices of the people who have enough entries
    valid_names = counts_by_name[counts_by_name >= NUM_ENTRIES_NEEDED_TO_COUNT].index

    # Filter the data to only include people with enough entries, then group by those people
    filtered_data_by_people = df[df['name'].isin(valid_names)].groupby('name')
    if len(filtered_data_by_people) == 0:
        return None

    # Get the mean of each person's accuracy and reaction time
    person_accuracy_averages = filtered_data_by_people['correct_guess'].mean()
    person_reaction_time_averages = filtered_data_by_people['reaction_time'].mean() / 1000
    # Weigh accuracy 2 times more than speed
    speed_and_accuracy_weighted_average =  person_accuracy_averages + (2-person_reaction_time_averages)/2
    # Sum the following formula to obtain a ranking:
    # Scales reaction time to seconds and looks at 2- reaction time and takes into account how many correct

    # Get the top 3 players
    top_3 = speed_and_accuracy_weighted_average.nlargest(3)

    # Convert to a dictionary with rankings
    rankings = {idx + 1: (name, round(score, 3)) for idx, (name, score) in enumerate(top_3.items())}

    return rankings

# Start at the home screen
@app.route('/')
def home():
    return render_template('index.html')

# Show the results page
@app.route('/results_page')
def show_results():
    results = load_results()
    generate_plot()  # Generate the plot before rendering
    leaderboard = get_curr_leader()
    print(f"leaderboard: {leaderboard}")
    return render_template('results.html', data=results, plot_file = PLOT_FILE, leaderboard=leaderboard)

# Called from JS to get the coherence and direction for each trial
@app.route('/start_trial', methods=['POST'])
def start_trial():
    """ Send a new trial's parameters to the frontend """
    coherence = round(random.uniform(COHERENCE_LOWER_BOUND, COHERENCE_UPPER_BOUND), 2)
    direction = random.choice(["left", "right"])
    return jsonify({"coherence": coherence, "direction": direction})

# Called from JS to save the user's response ("left" or "right")
@app.route('/submit_response', methods=['POST'])
def submit_response():
    """ Save the user's response """
    data = request.json
    name = data.get("name")
    user_response = data.get("response")
    correct_response = data.get("correct_response")
    coherence = data.get("coherence")
    reaction_time = data.get("reaction_time")


    is_correct = user_response == correct_response

    trial_result = {
        "name": name,
        "correct": correct_response,
        "user": user_response,
        "correct_guess": is_correct,
        "coherence": coherence * (1 if correct_response == "right" else -1),
            # Adjust the coherence to be negative if the dots moving to the left
            # and positive if the dots are moving to the right
        "reaction_time": min(reaction_time, 2000)  # Cap reaction time at 2000 ms
    }

    save_result(trial_result)
    return jsonify({"correct": is_correct})

# Allow users to download the results JSON file
@app.route('/download_results')
def download_results():
    """Allow users to download the results JSON file."""
    if os.path.exists(RESULTS_FILE):
        return send_file(RESULTS_FILE, as_attachment=True)
    else:
        return "No results available.", 404


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default to 5000 if PORT is not set, use 10000 when testing locally
    app.run(host='0.0.0.0', port=port)
