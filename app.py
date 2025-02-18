import json
import os
import random
from flask import Flask, request, jsonify, render_template
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend to prevent threading issues
import matplotlib.pyplot as plt

# Constants
# Constants
RESULTS_FILE = "results.json"
COHERENCE_LOWER_BOUND = 0.01
COHERENCE_UPPER_BOUND = 1.0
PLOT_FILE = "static/results_plot.png"

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
    trials = list(range(1, len(results) + 1))
    coherence = [r["coherence"] for r in results]  # Coherence level
    reaction_times = [r["reaction_time"] for r in results]  # Reaction time
    correct_guesses = [r["correct_guess"] for r in results]  # Boolean list of correctness
    # Assign colors based on correctness
    colors = ["green" if correct else "red" for correct in correct_guesses]
    plt.figure(figsize=(10, 5))
    # Scatter plot of Reaction Time vs Coherence (Green = Correct, Red = Incorrect)
    plt.subplot(2, 1, 1)
    plt.scatter(coherence, reaction_times, c=colors, edgecolors="black")
    plt.xlabel("Coherence (%)")
    plt.ylabel("Reaction Times (ms)")
    plt.title("Reaction Time vs Coherence")
    plt.ylim(0, 2000)  # Don't look at reaction times over 2000 ms
    plt.xlim(0, 1)
    plt.grid(True)
    # Scatter plot of Reaction Time over Trials
    plt.subplot(2, 1, 2)
    plt.scatter(trials, reaction_times, c=colors, edgecolors="black", label="Reaction Time (ms)")
    plt.xlabel("Trial Number")
    plt.ylabel("Reaction Time (ms)")
    plt.title("Reaction Time Over Trials")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("static/results_plot.png")
    plt.close()

# Start at the home screen
@app.route('/')
def home():
    return render_template('index.html')

# Show the results page
@app.route('/results_page')
def show_results():
    results = load_results()
    generate_plot()  # Generate the plot before rendering
    return render_template('results.html', data=results, plot_file = PLOT_FILE)

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
    user_response = data.get("response")
    correct_response = data.get("correct_response")
    coherence = data.get("coherence")
    reaction_time = data.get("reaction_time")

    is_correct = user_response == correct_response

    trial_result = {
        "correct": correct_response,
        "user": user_response,
        "correct_guess": is_correct,
        "coherence": coherence,
        "reaction_time": reaction_time
    }

    save_result(trial_result)
    return jsonify({"correct": is_correct})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default to 5000 if PORT is not set, use 10000 when testing locally
    app.run(host='0.0.0.0', port=port)
