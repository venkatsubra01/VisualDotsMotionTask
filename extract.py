import pandas as pd
import json

# Load the file
file_path = "class_data_missing.rtf"

# Read the contents of the file
with open(file_path, "r") as file:
    lines = file.readlines()

# Clean up the lines to remove unnecessary whitespace
lines = [line.strip() for line in lines if line.strip()]

# Define the expected column names
columns = ["name", "correct", "user", "correct_guess", "coherence", "reaction_time"]

# Process the data into a structured format
data = []
i = 0
for line in lines:
    parts = line.split()
    print(f"parts: {parts}")
    if len(parts) < 7:
        continue
    if parts[2] != "left" and parts[2] != "right":
        parts.remove(parts[2])
    entry = {
        "name": parts[1],
        "correct": parts[2],
        "user": parts[3],
        "correct_guess": parts[4] == "True",  # Convert string to boolean
        "coherence": float(parts[5]),  # Convert string to float
        "reaction_time": float(parts[6])  # Convert string to integer
    }

    data.append(entry)
    print(f"entry: {entry}")
print(f"data: {data}")


# Save the JSON output
json_file_path = "results.json"
with open(json_file_path, "w") as json_file:
    json.dump(data, json_file, indent=4)
