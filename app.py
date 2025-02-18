import json
import os
import pygame
import multiprocessing
import random
import math
from flask import Flask, request, jsonify, render_template
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend to prevent threading issues
import matplotlib.pyplot as plt


num_samples = 1000
UPDATE_INTERVAL = 100
dot_width = 2
dot_speed = 2  # 4 is fast, and 1 is slow
TRIAL_DURATION = 2000  # 2 seconds per trial
RESULTS_FILE = "results.json"
PLOT_FILE = "static/results_plot.png"
os.mkdir("static") if not os.path.exists("static") else None
COHERENCE_LOWER_BOUND = 0.01
COHERENCE_UPPER_BOUND = 1.0

app = Flask(__name__)


def set_dot_directions(dots, coherence, direction):
    random_indices = random.sample(range(num_samples), int(coherence * num_samples))
    for i in range(len(dots)):
        dot = dots[i]
        dot["coherent"] = False
        dot["angle"] = random.random() * 2 * math.pi

        if i in random_indices:
            dot["angle"] = direction
            dot["coherent"] = True
        else:
            dot["angle"] = random.random() * 2 * math.pi
            dot["coherent"] = False
    return dots


def save_result(trial_result):
    """ Appends a single trial result to the JSON file """
    # Load existing results or initialize an empty list
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as file:
            try:
                results = json.load(file)
            except json.JSONDecodeError:
                results = []
    else:
        results = []

    # Append new result
    results.append(trial_result)

    # Save updated list
    with open(RESULTS_FILE, "w") as file:
        json.dump(results, file, indent=4)


def load_results():
    """ Loads results from JSON file """
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []


import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend to prevent errors
import matplotlib.pyplot as plt

def generate_plot():
    """Generates scatter plots for performance over trials and saves it as an image."""
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
    plt.ylim(0, max(reaction_times) + 100)  # Adjust y-limit dynamically
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

def run_simulation():
    os.environ['SDL_VIDEODRIVER'] = 'cocoa'  # Ensure correct video driver
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Random Dots Motion Task")

    clock = pygame.time.Clock()
    running = True

    while running:
        coherence = random.uniform(COHERENCE_LOWER_BOUND, COHERENCE_UPPER_BOUND)
        direction = random.choice([0, 180])
        rad_direction = math.radians(direction)

        dots = [
            {
                "x": random.randint(0, 600),
                "y": random.randint(0, 600),
                "coherent": False,
                "angle": random.random() * 2 * math.pi,
            }
            for _ in range(num_samples)
        ]

        dots = set_dot_directions(dots, coherence, rad_direction)

        last_update_time = pygame.time.get_ticks()
        trial_start_time = pygame.time.get_ticks()
        user_response = None

        curr_time = pygame.time.get_ticks()
        while curr_time - trial_start_time < TRIAL_DURATION:
            screen.fill((0, 0, 0))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        user_response = "left"
                    elif event.key == pygame.K_RIGHT:
                        user_response = "right"

            current_time = pygame.time.get_ticks()
            if current_time - last_update_time >= UPDATE_INTERVAL:
                last_update_time = current_time
                dots = set_dot_directions(dots, coherence, rad_direction)

            for dot in dots:
                dot["x"] += dot_speed * math.cos(dot["angle"])
                dot["y"] += dot_speed * math.sin(dot["angle"])

                if dot["x"] < 0:
                    dot["x"] += 600
                elif dot["x"] > 600:
                    dot["x"] -= 600
                if dot["y"] < 0:
                    dot["y"] += 600
                elif dot["y"] > 600:
                    dot["y"] -= 600

                pygame.draw.circle(screen, (255, 255, 255), (int(dot["x"]), int(dot["y"])), dot_width)

            pygame.display.flip()
            clock.tick(60)

            if user_response:
                trial_end_time = pygame.time.get_ticks()
                correct_response = "left" if direction == 180 else "right"
                is_correct = user_response == correct_response
                reaction_time = trial_end_time - trial_start_time

                trial_result = {
                    "correct": correct_response,
                    "user": user_response,
                    "correct_guess": is_correct,
                    "coherence":coherence,
                    "reaction_time": reaction_time
                }

                # Save the result to JSON
                save_result(trial_result)

                flash_color = (0, 255, 0) if is_correct else (255, 0, 0)
                screen.fill(flash_color)
                pygame.display.flip()
                pygame.time.delay(500)
                curr_time = pygame.time.get_ticks()
                break
            curr_time = pygame.time.get_ticks()
        if curr_time - trial_start_time >= TRIAL_DURATION: # This means the user response was not fast enough
            correct_response = "left" if direction == 180 else "right"
            trial_result = {
                "correct": correct_response,
                "user": "no_response",
                "correct_guess": False,
                "coherence": coherence,
                "reaction_time": TRIAL_DURATION
            }
            save_result(trial_result)
            screen.fill((255, 0, 0))
            pygame.display.flip()
            pygame.time.delay(500)



@app.route('/')
def home():
    return render_template('index.html')


@app.route('/results_page')
def show_results():
    results = load_results()
    generate_plot()  # Generate the plot before rendering
    return render_template('results.html', data=results, plot_file=PLOT_FILE)


@app.route('/start', methods=['POST'])
def start_simulation():
    p = multiprocessing.Process(target=run_simulation)
    p.start()
    return jsonify({"message": "Simulation started!"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
