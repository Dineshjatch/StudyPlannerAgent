from datetime import datetime, timedelta
from memory import tasks
from agent_trace import log

priority_order = {"urgent": 0, "high": 1, "normal": 2}





def build_schedule(session_map=None):
    if not tasks:
        return []

    session_map = session_map or {}
    today = datetime.now().date()
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            priority_order.get(t.get("priority", "normal"), 2),
            datetime.strptime(t["due_date"], "%Y-%m-%d").date(),
        ),
    )

    schedule = []
    occupied = set()

    for task in sorted_tasks:
        due = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
        days_left = (due - today).days
        available_days = [
            today + timedelta(days=i)
            for i in range(max(days_left, 1))
        ]
        if not available_days:
            available_days = [today]

        

        sessions = task.get("sessions", 1)

        if not isinstance(sessions, int) or sessions < 1:
            sessions = 1

        sessions = min(sessions, len(available_days))

        if sessions == 1:
            chosen = [available_days[-1]]
        else:
            step = (len(available_days) - 1) / (sessions - 1)
            chosen = [available_days[round(i * step)] for i in range(sessions)]

        final_days = []
        for day in chosen:
            candidates = [day]
            for offset in range(1, len(available_days) + 1):
                candidates.extend([day + timedelta(days=offset), day - timedelta(days=offset)])
            candidate = next(
                (d for d in candidates if today <= d < due and d not in occupied),
                None,
            )
            if candidate is not None:
                occupied.add(candidate)
                final_days.append(candidate)

        for i, day in enumerate(final_days):
            label = task["name"]
            if i == len(final_days) - 1 and len(final_days) > 1:
                label += " (Revision)"
            schedule.append({
                "task": label,
                "study_day": day.isoformat(),
                "deadline": task["due_date"],
                "priority": task["priority"],
            })

    schedule.sort(key=lambda x: x["study_day"])
    log("build_schedule", f"{len(schedule)} sessions generated")
    return schedule
