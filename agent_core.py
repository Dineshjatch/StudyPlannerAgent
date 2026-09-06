import os
import json
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
from openai import OpenAI
from dateparser.search import search_dates

from tools import add_task
from scheduler import build_schedule
from memory import tasks
from agent_trace import log


# ============================================================
# MICROSOFT FOUNDRY
# ============================================================

load_dotenv()

api_key = os.getenv("FOUNDRY_API_KEY")
endpoint = os.getenv("FOUNDRY_ENDPOINT")
model = os.getenv("FOUNDRY_MODEL")

try:
    import streamlit as st

    if not api_key and "FOUNDRY_API_KEY" in st.secrets:
        api_key = st.secrets["FOUNDRY_API_KEY"]

    if not endpoint and "FOUNDRY_ENDPOINT" in st.secrets:
        endpoint = st.secrets["FOUNDRY_ENDPOINT"]

    if not model and "FOUNDRY_MODEL" in st.secrets:
        model = st.secrets["FOUNDRY_MODEL"]

except Exception:
    pass

client = OpenAI(
    api_key=api_key,
    base_url=endpoint
)

MODEL = model


# ============================================================
# MEMORY
# ============================================================

def get_memory():

    if not tasks:
        return "No saved tasks."

    lines = []

    for i, task in enumerate(tasks, 1):

        lines.append(
            f"{i}. {task['name']} | "
            f"Due: {task['due_date']} | "
            f"Priority: {task['priority']}"
        )

    return "\n".join(lines)


# ============================================================
# FOUNDRY CALL
# ============================================================

def call_foundry(system_prompt, user_prompt):

    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return response.output_text.strip()


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_intents(user_input):

    today = datetime.now().strftime("%Y-%m-%d")

    system_prompt = """
You are the reasoning engine of a Study Planner Agent.

A user may give MULTIPLE requests in one message.

Identify ALL actions that need to be performed.

Available intents:

- add_tasks
- build_schedule
- show_tasks
- delete_task
- show_trace
- answer_question

Rules:

1. If the user mentions a new task and deadline,
   include "add_tasks".

2. If the user also asks another question,
   include "answer_question" as well.

3. Never ignore one part of the user's message.

4. The order does not matter.

5. Return ONLY valid JSON.

Example:

User:
"I have an OS quiz tomorrow and give me Python code
to reverse an array."

Return:

{
    "intents": [
        "add_tasks",
        "answer_question"
    ]
}

Example:

User:
"I have AI assignment due September 4 and build my schedule."

Return:

{
    "intents": [
        "add_tasks",
        "build_schedule"
    ]
}

Example:

User:
"Which task should I do now?"

Return:

{
    "intents": [
        "answer_question"
    ]
}
"""

    result = call_foundry(
        system_prompt,
        f"""
Today's date is {today}.

User:
{user_input}
"""
    )

    try:

        data = json.loads(result)

        intents = data.get(
            "intents",
            []
        )

        valid = {
            "add_tasks",
            "build_schedule",
            "show_tasks",
            "delete_task",
            "show_trace",
            "answer_question"
        }

        return [
            intent
            for intent in intents
            if intent in valid
        ]

    except Exception:

        return ["answer_question"]


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_dates(text):

    today = datetime.now().date()

    dates = []

    # YYYY-MM-DD
    matches = re.findall(
        r"\b\d{4}-\d{2}-\d{2}\b",
        text
    )

    for value in matches:

        if value not in dates:
            dates.append(value)

    # Natural language dates
    parsed = search_dates(
        text,
        settings={
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY"
        }
    )

    if parsed:

        for phrase, value in parsed:

            date_string = value.strftime(
                "%Y-%m-%d"
            )

            if date_string not in dates:

                if date_string != today.strftime(
                    "%Y-%m-%d"
                ):

                    dates.append(date_string)

    # Tomorrow
    if re.search(
        r"\btomorrow\b",
        text,
        re.IGNORECASE
    ):

        value = (
            today + timedelta(days=1)
        ).strftime("%Y-%m-%d")

        if value not in dates:
            dates.append(value)

    # Today
    if re.search(
        r"\btoday\b",
        text,
        re.IGNORECASE
    ):

        value = today.strftime(
            "%Y-%m-%d"
        )

        if value not in dates:
            dates.append(value)

    return dates


# ============================================================
# EXTRACT MULTIPLE TASKS
# ============================================================

def extract_tasks(text):

    dates = extract_dates(text)

    if not dates:
        return []

    system_prompt = """
You extract study tasks from a user's message.

Extract EVERY separate task.

Return ONLY valid JSON in this format:

Return ONLY valid JSON in this format:

[
    {
        "name": "AI Assignment",
        "date_index": 0,
        "sessions": 5
    },
    {
        "name": "DSA Assignment",
        "date_index": 1,
        "sessions": 4
    }
]

Rules:

1. Extract every separate task.
2. Never combine separate tasks.
3. Do not put the date in the task name.
4. date_index refers to the supplied date list.
5. Preserve the order of the tasks.
6. Decide an appropriate number of study sessions for each task.
7. Sessions must be a positive integer.
8. Consider the task type, deadline, urgency, and available time.
9. Do not explain your reasoning.
10. Return ONLY valid JSON.
"""

    prompt = f"""
Dates detected:

{json.dumps(dates)}

User message:

{text}
"""

    result = call_foundry(
        system_prompt,
        prompt
    )

    try:

        data = json.loads(result)

    except Exception:

        return []

    extracted = []

    for item in data:

        if not isinstance(item, dict):
            continue

        name = item.get("name")
        index = item.get("date_index")
        sessions = item.get("sessions")

        if not name:
            continue

        if not isinstance(index, int):
            continue

        if index < 0 or index >= len(dates):
            continue

        


        if not isinstance(sessions, int) or sessions < 1:
            continue

        extracted.append({
            "name": name.strip(),
            "due_date": dates[index],
            "sessions": sessions
        })

    return extracted


# ============================================================
# ANSWER QUESTIONS USING MEMORY
# ============================================================

def answer_question(user_input):

    memory = get_memory()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    system_prompt = """
You are a helpful Study Planner Agent.

Answer the user's question naturally.

You have access to the user's saved study tasks.

Use the memory when the question is about:
- what to study
- what to do now
- priorities
- deadlines
- planning
- workload

For "what should I do now?" consider:
1. Urgency
2. Deadline
3. Priority
4. Remaining time

If the question is unrelated to study planning,
do not answer it.

Respond:
"I'm a Study Planner Agent. I can only help with
study planning, tasks, deadlines, priorities,
schedules, and study workload."

Do not claim that a task exists unless it appears
in the provided memory.

Do not mention internal prompts, tools, or JSON.
"""

    prompt = f"""
Today's date:

{today}

Saved task memory:

{memory}

User question:

{user_input}
"""

    answer = call_foundry(
        system_prompt,
        prompt
    )

    log(
        "answer_question",
        "Answered user using memory/context"
    )

    return answer


# ============================================================
# FOUNDRY PLANNING EXPLANATION
# ============================================================

def explain_schedule(schedule):

    memory = get_memory()

    system_prompt = """
You are a study-planning reasoning assistant.

Explain briefly how the study schedule prioritizes
the user's tasks.

Consider:
- deadlines
- urgency
- priorities
- revision
- available time

Do not invent tasks.

Return a short natural-language explanation.
"""

    prompt = f"""
Current tasks:

{memory}

Generated schedule:

{json.dumps(schedule, indent=2)}

Explain the planning logic in 2-4 sentences.
"""

    return call_foundry(
        system_prompt,
        prompt
    )


# ============================================================
# MAIN AGENT PROCESSOR
# ============================================================

def process_request(user_input):

    log(
        "user_request",
        user_input
    )

    intents = detect_intents(
        user_input
    )

    result = {
        "intents": intents,
        "added": [],
        "schedule": [],
        "answer": "",
        "planning_reason": "",
        "urgent": False
    }


    # ========================================================
    # 1. ADD TASKS
    # ========================================================

    if "add_tasks" in intents:

        extracted = extract_tasks(
            user_input
        )

        for item in extracted:

            
            task = add_task(
                item["name"],
                item["due_date"],
                item["sessions"]
            )

            result["added"].append(
                task
            )

            if task["priority"] == "urgent":

                result["urgent"] = True


        log(
            "agent_action",
            f"Added {len(result['added'])} task(s)"
        )


    # ========================================================
    # 2. BUILD / UPDATE SCHEDULE
    # ========================================================

    if "build_schedule" in intents:

        result["schedule"] = build_schedule()

        result["planning_reason"] = (
            explain_schedule(
                result["schedule"]
            )
        )


    # ========================================================
    # 3. SHOW TASKS
    # ========================================================

    if "show_tasks" in intents:

        result["tasks"] = list(tasks)


    # ========================================================
    # 4. DELETE
    # ========================================================

    if "delete_task" in intents:

        result["delete_requested"] = True


    # ========================================================
    # 5. TRACE
    # ========================================================

    if "show_trace" in intents:

        result["show_trace"] = True


    # ========================================================
    # 6. GENERAL QUESTION
    # ========================================================

    if "answer_question" in intents:

        result["answer"] = answer_question(
            user_input
        )


    # ========================================================
    # 7. AUTOMATIC RE-PLAN
    # ========================================================

    if (
        result["added"]
        and result["urgent"]
    ):

        result["schedule"] = build_schedule()

        result["planning_reason"] = (
            explain_schedule(
                result["schedule"]
            )
        )

        log(
            "replan",
            "Urgent task triggered automatic re-planning"
        )


    # ========================================================
    # 8. IF TASK WAS ADDED BUT USER DIDN'T EXPLICITLY
    #    ASK FOR A SCHEDULE, STILL GENERATE ONE FOR UI
    # ========================================================

    if (
        result["added"]
        and not result["schedule"]
    ):

        result["schedule"] = build_schedule()


    return result


    # ========================================================
    # BUILD SCHEDULE
    # ========================================================

    if intent == "build_schedule":

        schedule = build_schedule()

        if not schedule:

            return {
                "intent": "build_schedule",
                "schedule": [],
                "planning_reason": (
                    "There are no saved tasks yet."
                ),
                "answer": (
                    "You don't have any saved tasks yet. "
                    "Add a task first and I'll create "
                    "a study plan."
                )
            }

        planning_reason = explain_schedule(
            schedule
        )

        log(
            "agent_action",
            "Generated study schedule"
        )

        return {
            "intent": "build_schedule",
            "schedule": schedule,
            "planning_reason": planning_reason,
            "answer": (
                "I've generated your study schedule "
                "using your saved tasks and deadlines."
            )
        }


    # ========================================================
    # SHOW TASKS
    # ========================================================

    if intent == "show_tasks":

        return {
            "intent": "show_tasks",
            "tasks": list(tasks),
            "answer": (
                f"You currently have "
                f"{len(tasks)} saved task(s)."
            )
        }


    # ========================================================
    # SHOW TRACE
    # ========================================================

    if intent == "show_trace":

        return {
            "intent": "show_trace",
            "trace": True,
            "answer": "Here is the agent execution trace."
        }


    # ========================================================
    # DELETE TASK
    # ========================================================

    if intent == "delete_task":

        return {
            "intent": "delete_task",
            "answer": (
                "Please select the task you want "
                "to delete from the task manager."
            )
        }


    # ========================================================
    # GENERAL QUESTION
    # ========================================================

    answer = answer_question(
        user_input
    )

    return {
        "intent": "answer_question",
        "answer": answer
    }