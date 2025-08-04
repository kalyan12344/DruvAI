import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict
import asyncio

from langchain.tools import tool
from pydantic import BaseModel, Field
from firebase_admin import firestore

class CreateTaskInput(BaseModel):
    name: str = Field(description="The name or description of the task.")
    priority: str = Field(default="Medium", description="Priority: 'High', 'Medium', or 'Low'.")
    due_date: Optional[str] = Field(default=None, description="Due date in yyyy-MM-dd format.")

class DeleteTaskInput(BaseModel):
    name: str = Field(description="The exact name of the task to be deleted.")

class CheckTaskInput(BaseModel):
    name: str = Field(description="The title of the task to check for.")

def get_user_tasks_collection(db, user_id: str):
    return db.collection('users').document(user_id).collection('tasks')


@tool(args_schema=CreateTaskInput)
async def create_task_tool(*, name: str, priority: str = "Medium", due_date: Optional[str] = None, user_id: str) -> str:
    """Creates a new task for the user in their personal to-do list."""
    try:
        db = firestore.client()
        tasks_collection = get_user_tasks_collection(db, user_id)
        
        new_task = {
            "id": str(uuid.uuid4()), "name": name, "status": "To Do",
            "priority": priority, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
            "due_date": datetime.fromisoformat(due_date) if due_date else None
        }
        
        await asyncio.to_thread(tasks_collection.document(new_task["id"]).set, new_task)
        return f"Successfully created task: '{name}' with {priority} priority."
    except Exception as e:
        return f"Error creating task: {str(e)}"

@tool(args_schema=DeleteTaskInput)
async def delete_task_tool(*, name: str, user_id: str) -> str:
    """Deletes a task from the user's list by its exact name."""
    try:
        db = firestore.client()
        tasks_collection = get_user_tasks_collection(db, user_id)
        
        query = tasks_collection.where("name", "==", name).limit(1)
        docs_stream = await asyncio.to_thread(query.stream)
        task_to_delete = next(docs_stream, None)

        if not task_to_delete:
            return f"Error: Could not find a task named '{name}'."

        await asyncio.to_thread(task_to_delete.reference.delete)
        return f"Successfully deleted task: '{name}'."
    except Exception as e:
        return f"Error deleting task: {str(e)}"

@tool
async def list_all_tasks(*, user_id: str) -> List[Dict]:
    """Lists all of the user's current tasks."""
    try:
        db = firestore.client()
        tasks_collection = get_user_tasks_collection(db, user_id)
        docs_stream = await asyncio.to_thread(tasks_collection.stream)
        
        tasks = [doc.to_dict() for doc in docs_stream]
        if not tasks:
            return []
            
        priority_map = {"High": 1, "Medium": 2, "Low": 3}
        tasks.sort(key=lambda t: (priority_map.get(t.get('priority', 'Medium'), 4), t.get('due_date') or datetime.max))
        
        return [{"name": t['name'], "priority": t.get('priority'), "due_date": t.get('due_date')} for t in tasks]
    except Exception as e:
        return [{"error": f"Could not list tasks: {str(e)}"}]