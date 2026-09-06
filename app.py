import streamlit as st
from datetime import datetime

from agent_core import process_request
from memory import tasks, save_tasks
from scheduler import build_schedule
from agent_trace import show_trace


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Study Planner Agent",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background: #0E1229;
}

.hero {
    padding: 24px 28px;
    border: 1px solid #2B3266;
    border-left: 4px solid #E8A33D;
    border-radius: 10px;
    background: #171C3F;
    margin-bottom: 20px;
}

.hero h1 {
    margin: 0;
    color: #EDEFFA;
}

.hero p {
    color: #9AA0C9;
    margin: 6px 0 0;
}

.card {
    padding: 14px 16px;
    border: 1px solid #2B3266;
    border-radius: 8px;
    background: #171C3F;
    margin-bottom: 8px;
}

.agent-box {
    padding: 16px;
    border: 1px solid #3B478A;
    border-radius: 10px;
    background: #151A3A;
    margin-bottom: 12px;
}

.agent-title {
    color: #E8A33D;
    font-size: 18px;
    font-weight: 700;
}

.small-text {
    color: #9AA0C9;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="hero">
    <h1>Study Planner Agent</h1>
    <p>
        Microsoft Foundry reasoning • persistent memory •
        tool execution • adaptive scheduling
    </p>
</div>
""", unsafe_allow_html=True)


today = datetime.now().date()


# ============================================================
# SESSION STATE
# ============================================================

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

if "last_prompt" not in st.session_state:
    st.session_state["last_prompt"] = None


# ============================================================
# AGENT INPUT
# ============================================================

st.subheader("Ask the Agent")

st.caption(
    "Examples: "
    "“I have AI assignment due on 4 September 2026 and "
    "DSA assignment due on 8 September 2026”"
)


prompt = st.chat_input(
    "Ask your Study Planner Agent..."
)

if prompt:

    with st.spinner(
        "Microsoft Foundry is thinking..."
    ):

        try:

            result = process_request(prompt)

            st.session_state["last_result"] = result

        except Exception as e:

            st.error(
                f"Agent error: {e}"
            )

            st.session_state["last_result"] = None


# ============================================================
# PROCESS USER REQUEST
# ============================================================

if prompt:

    st.session_state["last_prompt"] = prompt


# ============================================================
# CURRENT AGENT RESULT
# ============================================================

result = st.session_state.get(
    "last_result"
)

if result:

    st.subheader(" Agent")

    # New agent_core returns "intents" (plural)
    intents = result.get("intents", [])

    # Backward compatibility if an older result is returned
    if not intents and result.get("intent"):
        intents = [result["intent"]]

    # --------------------------------------------------------
    # AGENT OUTPUT / ANSWER
    # --------------------------------------------------------

    answer = result.get("answer", "")

    if answer:
        st.markdown(
            """
            <div class="agent-box">
                <div class="agent-title">
                        Microsoft Foundry Agent
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(answer)

    # --------------------------------------------------------
    # ADD TASKS
    # --------------------------------------------------------

    added_tasks = result.get("added", [])

    if added_tasks:

        for task in added_tasks:

            icon = (
                "🚨"
                if task["priority"] == "urgent"
                else "⚠️"
                if task["priority"] == "high"
                else "📘"
            )

            st.success(
                f"{icon} Added **{task['name']}** — "
                f"due **{task['due_date']}** — "
                f"priority **{task['priority']}"
            )

    # --------------------------------------------------------
    # FOUNDRY PLANNING
    # --------------------------------------------------------

    planning_reason = result.get(
        "planning_reason",
        ""
    )

    if planning_reason:

        st.info(
            f" **Microsoft Foundry Planning**\n\n"
            f"{planning_reason}"
        )

    # --------------------------------------------------------
    # URGENT RE-PLAN
    # --------------------------------------------------------

    if result.get("urgent"):

        st.warning(
            " **Urgent task detected.** "
            "The agent automatically re-planned "
            "the existing study schedule."
        )

    # --------------------------------------------------------
    # SHOW TASKS
    # --------------------------------------------------------

    if "show_tasks" in intents:

        saved_tasks = result.get(
            "tasks",
            list(tasks)
        )

        st.markdown("### Saved Tasks")

        if saved_tasks:

            for i, task in enumerate(
                saved_tasks,
                1
            ):

                st.write(
                    f"{i}. {task['name']} — "
                    f"Due: {task['due_date']} — "
                    f"Priority: {task['priority']}"
                )

        else:

            st.info("No saved tasks.")

    # --------------------------------------------------------
    # DELETE REQUEST
    # --------------------------------------------------------

    if result.get("delete_requested"):

        st.info(
            "Use the Delete Task control on the right "
            "to select the task you want to remove."
        )

# ============================================================
# IMPORTANT:
# REBUILD SCHEDULE AFTER PROCESSING REQUEST
# ============================================================

# This is the key fix.
#
# The old version calculated the schedule BEFORE the user
# request was processed. Now we calculate it AFTER task
# additions/deletions.

schedule = build_schedule()


# ============================================================
# STATISTICS
# ============================================================

urgent_count = sum(
    t.get("priority") == "urgent"
    for t in tasks
)

high_count = sum(
    t.get("priority") == "high"
    for t in tasks
)

session_count = len(schedule)


st.divider()


c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "Tasks",
        len(tasks)
    )

with c2:

    st.metric(
        "Urgent",
        urgent_count
    )

with c3:

    st.metric(
        "High",
        high_count
    )

with c4:

    st.metric(
        "Sessions",
        session_count
    )


st.divider()


# ============================================================
# MAIN DASHBOARD
# ============================================================

left, right = st.columns(
    [1.15, 1]
)


# ============================================================
# LEFT COLUMN
# ============================================================

with left:

    # --------------------------------------------------------
    # TODAY'S FOCUS
    # --------------------------------------------------------

    st.subheader(
        "Today's Focus"
    )

    today_items = [
        item
        for item in schedule
        if item["study_day"]
        == today.isoformat()
    ]


    if today_items:

        for item in today_items:

            if item["priority"] == "urgent":
                icon = "🚨"

            elif item["priority"] == "high":
                icon = "⚠️"

            else:
                icon = "📘"


            st.markdown(
                f"""
                <div class="card">
                    <b>{icon} {item['task']}</b><br>
                    Deadline: {item['deadline']}<br>
                    Priority: {item['priority']}
                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.success(
            "No study session scheduled for today."
        )


    # --------------------------------------------------------
    # COMPLETE STUDY PLAN
    # --------------------------------------------------------

    st.subheader(
        "Complete Study Plan"
    )


    if schedule:

        for item in schedule:

            if item["priority"] == "urgent":
                icon = "🚨"

            elif item["priority"] == "high":
                icon = "⚠️"

            else:
                icon = "📘"


            day_label = item[
                "study_day"
            ]

            if day_label == today.isoformat():

                day_label += " • TODAY"


            st.markdown(
                f"""
                <div class="card">
                    <b>{day_label}</b>
                    · {icon}
                    <b>{item['task']}</b><br>
                    Deadline: {item['deadline']}
                    · Priority: {item['priority']}
                </div>
                """,
                unsafe_allow_html=True
            )


    else:

        st.info(
            "Add tasks to generate a study plan."
        )


# ============================================================
# RIGHT COLUMN
# ============================================================

with right:

    # --------------------------------------------------------
    # PERSISTENT MEMORY
    # --------------------------------------------------------

    st.subheader(
        "Persistent Memory"
    )


    if tasks:

        for i, task in enumerate(
            tasks,
            1
        ):

            if task["priority"] == "urgent":
                icon = "🚨"

            elif task["priority"] == "high":
                icon = "⚠️"

            else:
                icon = "📘"


            st.markdown(
                f"""
                <div class="card">
                    {i}. {icon}
                    <b>{task['name']}</b><br>
                    Due: {task['due_date']}
                    · {task['priority']}
                </div>
                """,
                unsafe_allow_html=True
            )


    else:

        st.info(
            "No saved tasks."
        )


    # --------------------------------------------------------
    # DELETE TASK
    # --------------------------------------------------------

    if tasks:

        st.subheader(
            "Delete Task"
        )

        options = [
            f"{i + 1}. {t['name']} "
            f"({t['due_date']})"
            for i, t in enumerate(tasks)
        ]


        selected = st.selectbox(
            "Select task",
            options,
            label_visibility="collapsed"
        )


        if st.button(
            "Delete Selected",
            use_container_width=True
        ):

            index = options.index(
                selected
            )

            removed = tasks.pop(
                index
            )

            save_tasks()

            # Clear previous response because
            # memory has changed.
            st.session_state[
                "last_result"
            ] = None

            st.success(
                f"Deleted **{removed['name']}**."
            )

            st.rerun()


    # --------------------------------------------------------
    # AGENT TRACE
    # --------------------------------------------------------

    st.subheader(
        "Agent Trace"
    )

    trace = show_trace()


    if trace:

        for item in trace[-10:]:

            st.code(
                f"{item['time']} | "
                f"{item['step']} | "
                f"{item['details']}"
            )

    else:

        st.caption(
            "No actions recorded yet."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Microsoft Foundry is the reasoning layer • "
    "Python tools execute actions • "
    "tasks.json provides persistent memory"
)