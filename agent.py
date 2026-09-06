from agent_core import process_request
from memory import tasks, save_tasks


def print_result(result):
    intent = result.get("intent")

    if intent == "add_tasks":
        print("\nAgent: Tasks added successfully.")
        for task in result.get("added", []):
            print(f"✓ {task['name']} | Due: {task['due_date']} | Priority: {task['priority']}")
        if result.get("urgent"):
            print("\n🚨 Urgent task detected. Schedule automatically re-planned.")
        print("\nUpdated schedule:")
        for item in result.get("schedule", []):
            print(f"- {item['study_day']} → {item['task']} | Due: {item['deadline']} | {item['priority']}")

    elif intent == "build_schedule":
        print("\nStudy Schedule:")
        schedule = result.get("schedule", [])
        if not schedule:
            print("No saved tasks.")
        for item in schedule:
            print(f"- {item['study_day']} → {item['task']} | Due: {item['deadline']} | {item['priority']}")
        if result.get("planning_reason"):
            print(f"\nFoundry planning: {result['planning_reason']}")

    elif intent == "show_tasks":
        print("\nSaved Tasks:")
        if not result.get("tasks"):
            print("No saved tasks.")
        for i, task in enumerate(result["tasks"], 1):
            print(f"{i}. {task['name']} | Due: {task['due_date']} | Priority: {task['priority']}")

    elif intent == "show_trace":
        print("\nAgent Trace:")
        for item in result.get("trace", []):
            print(item)

    elif intent == "delete_task":
        print("\nSaved Tasks:")
        if not result.get("tasks"):
            print("No tasks to delete.")
            return
        for i, task in enumerate(result["tasks"], 1):
            print(f"{i}. {task['name']} | Due: {task['due_date']}")
        try:
            index = int(input("Enter task number to delete: ")) - 1
            if 0 <= index < len(tasks):
                removed = tasks.pop(index)
                save_tasks()
                print(f"Deleted: {removed['name']}")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid number.")

    else:
        print("\nAgent:")
        print(result.get("answer", result.get("message", "I could not process that request.")))


print("\n=== Study Planner Agent | Microsoft Foundry ===")
print("Type 'exit' to quit.")

while True:
    user = input("\nYou: ").strip()
    if user.lower() == "exit":
        break
    if not user:
        continue
    try:
        print_result(process_request(user))
    except Exception as exc:
        print(f"\nAgent error: {exc}")
