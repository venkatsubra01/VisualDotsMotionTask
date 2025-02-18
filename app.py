import json
import os
import random
from flask import Flask, request, jsonify, render_template

# Constants
RESULTS_FILE = "results.json"
COHERENCE_LOWER_BOUND = 0.01
COHERENCE_UPPER_BOUND = 1.0
PLOT_FILE = "static/results_plot.png"

app = Flask(__name__)

# Ensure static directory exists
if not os.path.exists("static"):
    os.mkdir("static")


def save_result(trial_result):
    """ Append a single trial result to the JSON file """
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as file:
            try:
                results = json.load(file)
            except json.JSONDecodeError:
                results = []
    else:
        results = []

    results.append(trial_result)

    with open(RESULTS_FILE, "w") as file:
        json.dump(results, file, indent=4)


def load_results():
    """ Load results from JSON file """
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/results_page')
def show_results():
    results = load_results()
    return render_template('results.html', data=results, plot_file = PLOT_FILE)


@app.route('/start_trial', methods=['POST'])
def start_trial():
    """ Send a new trial's parameters to the frontend """
    coherence = round(random.uniform(COHERENCE_LOWER_BOUND, COHERENCE_UPPER_BOUND), 2)
    direction = random.choice(["left", "right"])
    return jsonify({"coherence": coherence, "direction": direction})


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
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(host='0.0.0.0', port=port)
