#api/routes/tasks.py
import json
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()

# --- Data Storage ---
# We'll use a dedicated JSON file to store our tasks.
TASKS_DB_FILE = "tasks.json"

# --- Pydantic Models for Data Validation ---

class Task(BaseModel):
    """
    Represents a single task with all its properties.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: str = "To Do"  # Default status
    priority: str = "Medium" # Default priority
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TaskUpdate(BaseModel):
    """
    A model for updating an existing task. All fields are optional.
    """
    name: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


# --- Helper Functions for Reading/Writing to the JSON file ---

def read_tasks() -> List[Task]:
    """Reads all tasks from the tasks.json file."""
    try:
        with open(TASKS_DB_FILE, 'r') as f:
            tasks_data = json.load(f)
            # Use Pydantic to validate and convert the data into Task objects
            return [Task(**task) for task in tasks_data]
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is empty, return an empty list
        return []

def write_tasks(tasks: List[Task]):
    """Writes the full list of tasks to the tasks.json file."""
    with open(TASKS_DB_FILE, 'w') as f:
        # Convert the list of Pydantic Task objects back to a JSON-serializable format
        json.dump([task.dict() for task in tasks], f, indent=4, default=str)


# --- API Endpoints for Task Management ---

@router.post("/add", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: Task):
    """
    Creates a new task and adds it to the database.
    """
    tasks = read_tasks()
    tasks.append(task)
    write_tasks(tasks)
    return task

@router.get("/retrieve", response_model=List[Task])
def get_all_tasks():
    """
    Retrieves a list of all tasks.
    """
    return read_tasks()

@router.get("/retrieve/{task_id}", response_model=Task)
def get_task(task_id: str):
    """
    Retrieves a single task by its ID.
    """
    tasks = read_tasks()
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@router.put("/update/{task_id}", response_model=Task)
def update_task(task_id: str, task_update: TaskUpdate):
    """
    Updates an existing task by its ID.
    """
    tasks = read_tasks()
    task_to_update = None
    for task in tasks:
        if task.id == task_id:
            task_to_update = task
            break

    if not task_to_update:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update the task with the provided data
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task_to_update, key, value)
    
    # Update the 'updated_at' timestamp
    task_to_update.updated_at = datetime.utcnow()

    write_tasks(tasks)
    return task_to_update

@router.delete("/delete/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str):
    """
    Deletes a task by its ID.
    """
    tasks = read_tasks()
    task_to_delete = None
    for task in tasks:
        if task.id == task_id:
            task_to_delete = task
            break

    if not task_to_delete:
        raise HTTPException(status_code=404, detail="Task not found")

    tasks.remove(task_to_delete)
    write_tasks(tasks)
    return
