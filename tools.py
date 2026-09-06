from memory import tasks, save_tasks
from datetime import datetime
from agent_trace import log


def add_task(name, due_date, sessions):

    if not isinstance(sessions, int) or sessions < 1:
        sessions = 1

    # Prevent accidental duplicate tasks
    for existing in tasks:

        if (
            existing["name"].strip().lower()
            == name.strip().lower()
            and existing["due_date"]
            == due_date
        ):

            log(
                "add_task",
                f"Duplicate ignored: {name}"
            )

            return existing

    due = datetime.strptime(
        due_date,
        "%Y-%m-%d"
    ).date()

    today = datetime.now().date()

    days_left = (due - today).days

    if days_left <= 1:
        priority = "urgent"
    elif days_left <= 3:
        priority = "high"
    else:
        priority = "normal"

    

    task = {
        "name": name.strip(),
        "due_date": due_date,
        "priority": priority,
        "sessions": sessions,
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    }

    tasks.append(task)

    save_tasks()

    log(
        "add_task",
        f"{name} ({priority})"
    )

    return task