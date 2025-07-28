#api/routes/remainders.py
import json
import uuid
from datetime import datetime, timedelta, time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from core.google_auth import get_calendar_service
from api.routes.auth import User, get_current_user

router = APIRouter()

# --- Data Storage ---
REMINDERS_DB_FILE = "reminders.json"

# --- Pydantic Models for Data Validation ---
class Reminder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    remind_at: datetime
    status: str = "Pending" # Pending, Completed
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- Helper Functions for File I/O ---
def read_reminders() -> List[Reminder]:
    """Reads all reminders from the reminders.json file."""
    try:
        with open(REMINDERS_DB_FILE, 'r') as f:
            reminders_data = json.load(f)
            return [Reminder(**r) for r in reminders_data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_reminders(reminders: List[Reminder]):
    """Writes the full list of reminders to the reminders.json file."""
    with open(REMINDERS_DB_FILE, 'w') as f:
        json.dump([r.dict() for r in reminders], f, indent=4, default=str)

# --- API Endpoints for Reminder Management ---
@router.post("/add", response_model=Reminder, status_code=status.HTTP_201_CREATED)
def create_reminder(reminder: Reminder, current_user: User = Depends(get_current_user)):
    """
    Creates a new reminder, saves it locally, AND adds it to the authenticated user's Google Calendar.
    """
    reminders = read_reminders()
    reminders.append(reminder)
    write_reminders(reminders)
    print(f"--- Reminder '{reminder.title}' saved locally for user {current_user.uid}. ---")

    try:
        print(f"--- Adding reminder to Google Calendar for user {current_user.uid}... ---")
        calendar_service = get_calendar_service(user_id=current_user.uid)
        
        event_body = {
            'summary': f"Reminder: {reminder.title}",
            'start': {
                'dateTime': reminder.remind_at.isoformat(),
                'timeZone': 'America/Chicago',
            },
            'end': {
                'dateTime': (reminder.remind_at + timedelta(minutes=30)).isoformat(),
                'timeZone': 'America/Chicago',
            },
            'reminders': { 'useDefault': True },
        }
        
        created_event = calendar_service.events().insert(
            calendarId='primary', 
            body=event_body
        ).execute()
        
        print(f"--- Google Calendar event created successfully. Event ID: {created_event.get('id')} ---")

    except Exception as e:
        print(f"--- CRITICAL ERROR: Could not create Google Calendar event for user {current_user.uid}. {e} ---")
        pass

    return reminder

@router.get("/list", response_model=List[Reminder])
def get_all_reminders():
    """Retrieves a list of all reminders."""
    return read_reminders()

@router.delete("/delete/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: str, current_user: User = Depends(get_current_user)):
    """
    Deletes a reminder and the corresponding event from the authenticated user's Google Calendar.
    """
    reminders = read_reminders()
    reminder_to_delete = next((r for r in reminders if r.id == reminder_id), None)

    if not reminder_to_delete:
        raise HTTPException(status_code=404, detail="Reminder not found")

    try:
        print(f"--- Attempting to delete Google Calendar event for user: {current_user.uid} ---")
        calendar_service = get_calendar_service(user_id=current_user.uid)

        reminder_date = reminder_to_delete.remind_at.date()
        time_min = datetime.combine(reminder_date, time.min).isoformat() + 'Z'
        time_max = datetime.combine(reminder_date, time.max).isoformat() + 'Z'

        events_result = calendar_service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        event_to_delete_calendar = None
        expected_title = f"Reminder: {reminder_to_delete.title}"
        for event in events:
            if event.get('summary') == expected_title:
                event_to_delete_calendar = event
                break
        
        if event_to_delete_calendar:
            event_id = event_to_delete_calendar['id']
            print(f"--- Found matching event. Deleting event ID: {event_id} ---")
            calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
            print("--- Google Calendar event deleted successfully. ---")
        else:
            print(f"--- INFO: No matching Google Calendar event found for '{expected_title}' on {reminder_date}. ---")

    except Exception as e:
        print(f"--- WARNING: An unexpected error occurred while deleting calendar event for user {current_user.uid}. {e} ---")

    reminders.remove(reminder_to_delete)
    write_reminders(reminders)
    return