import uuid
import asyncio
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from firebase_admin import firestore

from api.routes.auth import User, get_current_user

router = APIRouter()

# --- Pydantic Models for Data Validation ---
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: str = "To Do"
    priority: str = "Medium"
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

# --- API Endpoints for Task Management using Firestore ---

def get_user_tasks_collection(db, user_id: str):
    """Helper to get a reference to the user's tasks subcollection."""
    return db.collection('users').document(user_id).collection('tasks')

@router.post("/add", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task: Task, current_user: User = Depends(get_current_user)):
    """Creates a new task in the authenticated user's Firestore collection."""
    try:
        db = firestore.client()
        tasks_collection = get_user_tasks_collection(db, current_user.uid)
        await asyncio.to_thread(tasks_collection.document(task.id).set, task.model_dump())
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retrieve", response_model=List[Task])
async def get_all_tasks(current_user: User = Depends(get_current_user)):
    """Retrieves all tasks for the authenticated user from Firestore."""
    try:
        db = firestore.client()
        tasks_collection = get_user_tasks_collection(db, current_user.uid)
        docs_stream = await asyncio.to_thread(tasks_collection.stream)
        return [doc.to_dict() for doc in docs_stream]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate, current_user: User = Depends(get_current_user)):
    """Updates an existing task for the authenticated user."""
    db = firestore.client()
    task_ref = get_user_tasks_collection(db, current_user.uid).document(task_id)
    
    if not (await asyncio.to_thread(task_ref.get)).exists:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await asyncio.to_thread(task_ref.update, update_data)
    
    updated_doc = await asyncio.to_thread(task_ref.get)
    return updated_doc.to_dict()

@router.delete("/delete/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, current_user: User = Depends(get_current_user)):
    """Deletes a task by its ID for the authenticated user."""
    db = firestore.client()
    task_ref = get_user_tasks_collection(db, current_user.uid).document(task_id)

    if not (await asyncio.to_thread(task_ref.get)).exists:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await asyncio.to_thread(task_ref.delete)
    return
