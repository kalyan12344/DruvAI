import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from firebase_admin import firestore

# Import your user model and authentication dependency
from api.routes.auth import User, get_current_user

router = APIRouter()

# --- Pydantic Models for Data Validation (can remain mostly the same) ---

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str = "" # HTML content from the editor
    snippet: str = "" # Plain text snippet for the list view
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    snippet: Optional[str] = None

# --- API Endpoints using Firebase Firestore ---

@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note(note: Note, current_user: User = Depends(get_current_user)):
    """
    Creates a new note for the currently authenticated user in Firestore.
    """
    print("notes creation api called", current_user)
    try:
        db = firestore.client()
        # Create a new note document in the user's 'notes' subcollection
        db.collection('users').document(current_user.uid).collection('notes').document(note.id).set(note.dict())
        return note
    except Exception as e:
        print(f"🔥 FAILED TO CREATE NOTE. ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create note: {e}")


@router.get("/notes", response_model=List[Note])
def get_all_notes(current_user: User = Depends(get_current_user)):
    """
    Retrieves all notes for the currently authenticated user from Firestore,
    sorted by most recently updated.
    """
    try:
        db = firestore.client()
        notes_ref = db.collection('users').document(current_user.uid).collection('notes')
        
        # Order notes by 'updated_at' in descending order
        query = notes_ref.order_by("updated_at", direction=firestore.Query.DESCENDING)
        docs = query.stream()
        
        notes = [Note(**doc.to_dict()) for doc in docs]
        return notes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notes: {e}")

@router.get("/{note_id}", response_model=Note)
def get_note(note_id: str, current_user: User = Depends(get_current_user)):
    """
    Retrieves a single note by its ID for the currently authenticated user.
    """
    try:
        db = firestore.client()
        note_ref = db.collection('users').document(current_user.uid).collection('notes').document(note_id)
        doc = note_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return Note(**doc.to_dict())
    except Exception as e:
        # Re-raise HTTPException to preserve status code
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to retrieve note: {e}")

@router.put("/{note_id}", response_model=Note)
def update_note(note_id: str, note_update: NoteUpdate, current_user: User = Depends(get_current_user)):
    """
    Updates a note for the currently authenticated user in Firestore.
    """
    try:
        db = firestore.client()
        note_ref = db.collection('users').document(current_user.uid).collection('notes').document(note_id)

        # Prepare update data, excluding fields that weren't sent
        update_data = note_update.dict(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update information provided.")
            
        # Always update the 'updated_at' timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        note_ref.update(update_data)
        
        # Get the updated document to return the full object
        updated_doc = note_ref.get()
        if not updated_doc.exists:
             raise HTTPException(status_code=404, detail="Note not found after update.")

        return Note(**updated_doc.to_dict())
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to update note: {e}")


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: str, current_user: User = Depends(get_current_user)):
    """
    Deletes a note by its ID for the currently authenticated user.
    """
    try:
        db = firestore.client()
        note_ref = db.collection('users').document(current_user.uid).collection('notes').document(note_id)
        
        # To prevent deleting something that doesn't exist and returning success,
        # we can check if it exists first (optional but good practice).
        if not note_ref.get().exists:
            raise HTTPException(status_code=404, detail="Note not found")
            
        note_ref.delete()
        return
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {e}")