# Study Planner Agent

An AI-powered Study Planner Agent built for **CSE476 – Agentic AI and Intelligent Automation**.

The agent uses **Microsoft Foundry** as its reasoning layer to understand natural-language study requests, identify tasks and deadlines, determine the required number of study sessions, manage persistent task memory, generate study schedules, and automatically re-plan when urgent tasks are added.

## Features

- Microsoft Foundry GPT-4.1 Mini integration
- Natural-language task and deadline extraction
- AI-based study session estimation
- Tool-based task management
- Persistent memory using JSON
- Automatic study scheduling
- Priority-based task planning
- Automatic re-planning when urgent tasks are added
- Streamlit dashboard
- Terminal-based agent
- Agent execution trace
- Jupyter notebook demonstration

## How the Agent Works

The agent follows the workflow:

User Request  
→ Microsoft Foundry  
→ Intent and Task Understanding  
→ Session Estimation  
→ Tool Execution  
→ Persistent Memory  
→ Schedule Generation  
→ Re-planning when required

Microsoft Foundry acts as the reasoning layer, while Python tools perform deterministic operations such as storing tasks and generating the study schedule.

## Microsoft Foundry Integration

Microsoft Foundry is responsible for understanding the user's natural-language request and reasoning about the study workload.

For each new task, the model identifies:

- Task name
- Deadline
- Required number of study sessions

For example:

```json
{
    "name": "AI Assignment",
    "due_date": "2026-09-04",
    "sessions": 5
}