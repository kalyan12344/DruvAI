import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict

from langchain.tools import tool
from pydantic import BaseModel, Field

# --- Pydantic Models for Tool Inputs ---

class CreateTaskInput(BaseModel):
    """Input model for the create_task_tool."""
    name: str = Field(description="The name or description of the task.")
    priority: str = Field(description="The priority of the task, which can be 'High', 'Medium', or 'Low'.", default="Medium")
    due_date: Optional[str] = Field(description="The due date for the task in yyyy-MM-dd format.", default=None)

class DeleteTaskInput(BaseModel):
    """Input model for the delete_task_tool."""
    name: str = Field(description="The exact name of the task to be deleted.")

class CheckTaskInput(BaseModel):
    """Input model for the check_task_exists tool."""
    name: str = Field(description="The title of the task to check for.")


# --- Task Management Tools ---

@tool("create_task_tool", args_schema=CreateTaskInput)
def create_task_tool(name: str, priority: str = "Medium", due_date: Optional[str] = None) -> str:
    """
    Creates a new task with a name, priority, and optional due date,
    and saves it to the user's task list. Use this tool whenever a user
    asks to create a new to-do or task.
    """
    print(f"--- TOOL: Running create_task_tool for: {name} ---")
    
    try:
        tasks_db_file = "tasks.json"
        try:
            with open(tasks_db_file, 'r') as f:
                tasks = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            tasks = []
        
        due_date_iso = datetime.fromisoformat(due_date).isoformat() if due_date else None

        new_task = {
            "id": str(uuid.uuid4()),
            "name": name,
            "status": "To Do",
            "priority": priority,
            "due_date": due_date_iso,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        tasks.append(new_task)
        
        with open(tasks_db_file, 'w') as f:
            json.dump(tasks, f, indent=4)
            
        return f"Successfully created task: '{name}' with {priority} priority."

    except Exception as e:
        return f"An unexpected error occurred while creating the task: {str(e)}"

@tool("delete_task_tool", args_schema=DeleteTaskInput)
def delete_task_tool(name: str) -> str:
    """
    Deletes a task from the user's task list based on its exact name.
    Use this tool when a user asks to delete, remove, or complete a task.
    """
    print(f"--- TOOL: Running delete_task_tool for: {name} ---")
    
    tasks_db_file = "tasks.json"
    try:
        with open(tasks_db_file, 'r') as f:
            tasks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Error: Could not find the tasks list."

    task_to_delete = None
    for task in tasks:
        if task.get("name", "").lower() == name.lower():
            task_to_delete = task
            break

    if not task_to_delete:
        return f"Error: Could not find a task named '{name}'."

    tasks.remove(task_to_delete)
    
    with open(tasks_db_file, 'w') as f:
        json.dump(tasks, f, indent=4)

    return f"Successfully deleted task: '{name}'."

@tool("check_task_exists", args_schema=CheckTaskInput)
def check_task_exists(name: str) -> str:
    """
    Checks if a task with a specific title already exists in the user's list.
    """
    print(f"--- TOOL: Running check_task_exists for: {name} ---")
    
    tasks_db_file = "tasks.json"
    try:
        with open(tasks_db_file, 'r') as f:
            tasks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Could not access the tasks list."

    found_task = None
    for task in tasks:
        if task.get("name", "").lower() == name.lower():
            found_task = task
            break

    if found_task:
        due_date_str = "no due date."
        if found_task.get("due_date"):
            due_date = datetime.fromisoformat(found_task['due_date']).strftime('%A, %B %d')
            due_date_str = f"a due date of {due_date}."
        return f"Yes, you have a task for '{name}' with {found_task['priority']} priority and {due_date_str}"
    else:
        return f"No, you do not have a task set for '{name}'."

@tool
def list_all_tasks() -> List[Dict]:
    """
    Lists all current tasks from the user's list, sorted by priority and due date.
    Use this when a user asks a general question like 'what are my tasks?'
    """
    print(f"--- TOOL: Running list_all_tasks ---")
    
    tasks_db_file = "tasks.json"
    try:
        with open(tasks_db_file, 'r') as f:
            tasks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    if not tasks:
        return []

    priority_map = {"High": 1, "Medium": 2, "Low": 3}
    tasks.sort(key=lambda t: (priority_map.get(t.get('priority', 'Medium'), 4), t.get('due_date') or '9999-12-31'))
    
    formatted_list = []
    for task in tasks:
        due_date_str = ""
        if task.get("due_date"):
            due_date_str = datetime.fromisoformat(task['due_date']).strftime('%b %d')
        
        formatted_list.append({
            "name": task['name'],
            "priority": task.get('priority', 'Medium'),
            "due_date": due_date_str
        })
        
    return formatted_list
