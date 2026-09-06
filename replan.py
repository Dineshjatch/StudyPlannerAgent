from scheduler import build_schedule
from memory import tasks
from agent_trace import log


def replan_schedule():
    urgent_tasks = [t for t in tasks if t.get("priority") == "urgent"]
    schedule = build_schedule()
    log("replan_schedule", "Urgent task detected; schedule rebuilt")
    return {
        "success": True,
        "schedule": schedule,
        "urgent_count": len(urgent_tasks),
        "message": f"Schedule updated because {len(urgent_tasks)} urgent task(s) were detected.",
    }
