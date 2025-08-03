import uuid
from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict
from firebase_admin import storage, firestore

from lc.react_agent import run_agent
from lc.document_processor import index_document_in_background
from api.routes.auth import User, get_current_user

router = APIRouter()

class AgentQuery(BaseModel):
    input: dict | str
    context: Optional[Dict] = None

@router.post("/ask")
async def ask_agent(query: AgentQuery, current_user: User = Depends(get_current_user)):
    """Handles text-only queries for the agent."""
    output_dict = await run_agent(
        user_input=query.input,
        user=current_user,
        context=query.context
    )
    return output_dict

@router.post("/ask_with_file")
async def ask_agent_with_file(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    prompt: str = Form(""),
    file: UploadFile = File(...)
):
    """
    Handles file uploads, starts background indexing, and returns a document ID.
    """
    try:
        db = firestore.client()
        # Create a document in Firestore to track the processing status
        doc_ref = db.collection('users').document(current_user.uid).collection('documents').document()
        doc_ref.set({"filename": file.filename, "status": "Uploading...", "added_at": firestore.SERVER_TIMESTAMP})

        # Upload the file to Firebase Storage
        unique_filename = f"{doc_ref.id}_{file.filename}"
        file_path = f"user_uploads/{current_user.uid}/{unique_filename}"
        bucket = storage.bucket()
        blob = bucket.blob(file_path)
        blob.upload_from_file(file.file, content_type=file.content_type)
        
        doc_ref.update({"status": "Processing", "storage_path": file_path})

        # Start the slow indexing process in the background
        background_tasks.add_task(
            index_document_in_background,
            user_id=current_user.uid,
            document_id=doc_ref.id,
            file_path=file_path,
            original_filename=file.filename
        )
        
        # Immediately return the document ID to the frontend
        return {"document_id": doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))