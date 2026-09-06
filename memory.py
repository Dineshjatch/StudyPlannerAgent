import json
from pathlib import Path

# Always store tasks.json beside this Python file
TASK_FILE = Path(__file__).resolve().parent / "tasks.json"


def load_tasks():
    if not TASK_FILE.exists():
        return []

    try:
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


tasks = load_tasks()


def save_tasks():
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=4)