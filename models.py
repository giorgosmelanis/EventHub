import json
import os

# File paths
USERS_FILE = "users.json"
EVENTS_FILE = "events.json"

# Ensure JSON files exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

if not os.path.exists(EVENTS_FILE):
    with open(EVENTS_FILE, "w") as f:
        json.dump([], f)

def load_file(file_path):
    """Load data from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error loading {file_path}: {e}")
        return []

def save_file(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_users():
    """Load users from the JSON file."""
    return load_file(USERS_FILE)

def save_users(users):
    """Save users to the JSON file."""
    save_file(USERS_FILE, users)

def load_events():
    """Load events from the JSON file."""
    return load_file(EVENTS_FILE)

def save_events(events):
    """Save events to the JSON file."""
    save_file(EVENTS_FILE, events)