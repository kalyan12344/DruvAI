import json
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()

# --- Data Storage ---
NOTES_DB_FILE = "notes.json"

# --- Pydantic Models for Data Validation ---

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

# --- Helper Functions for File I/O ---

def read_notes() -> List[Note]:
    """Reads all notes from the notes.json file."""
    try:
        with open(NOTES_DB_FILE, 'r') as f:
            notes_data = json.load(f)
            return [Note(**note) for note in notes_data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_notes(notes: List[Note]):
    """Writes the full list of notes to the notes.json file."""
    with open(NOTES_DB_FILE, 'w') as f:
        json.dump([note.dict() for note in notes], f, indent=4, default=str)

# --- API Endpoints for Note Management ---

@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note(note: Note):
    """Creates a new, empty note."""
    notes = read_notes()
    notes.insert(0, note) # Add new notes to the top of the list
    write_notes(notes)
    return note

@router.get("/notes", response_model=List[Note])
def get_all_notes():
    """Retrieves all notes, sorted by most recently updated."""
    notes = read_notes()
    notes.sort(key=lambda n: n.updated_at, reverse=True)
    return notes

@router.get("/notes/{note_id}", response_model=Note)
def get_note(note_id: str):
    """Retrieves the full content of a single note by its ID."""
    notes = read_notes()
    for note in notes:
        if note.id == note_id:
            return note
    raise HTTPException(status_code=404, detail="Note not found")

@router.put("/notes/{note_id}", response_model=Note)
def update_note(note_id: str, note_update: NoteUpdate):
    """Updates a note's title or content."""
    notes = read_notes()
    note_to_update = None
    for note in notes:
        if note.id == note_id:
            note_to_update = note
            break

    if not note_to_update:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = note_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note_to_update, key, value)
    
    note_to_update.updated_at = datetime.utcnow()
    write_notes(notes)
    return note_to_update

@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: str):
    """Deletes a note by its ID."""
    notes = read_notes()
    initial_count = len(notes)
    notes = [note for note in notes if note.id != note_id]

    if len(notes) == initial_count:
        raise HTTPException(status_code=404, detail="Note not found")

    write_notes(notes)
    return
