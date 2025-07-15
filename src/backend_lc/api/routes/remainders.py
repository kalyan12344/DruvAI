import json
import uuid
from datetime import datetime, timedelta, time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Import the Google Calendar service getter
from core.google_auth import get_calendar_service

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
def create_reminder(reminder: Reminder):
    """
    Creates a new reminder, saves it locally, AND adds it to Google Calendar.
    """
    # 1. Save the reminder to our local JSON database
    reminders = read_reminders()
    reminders.append(reminder)
    write_reminders(reminders)
    print(f"--- Reminder '{reminder.title}' saved locally. ---")

    # 2. Create the corresponding event on Google Calendar
    try:
        print(f"--- Adding reminder to Google Calendar... ---")
        calendar_service = get_calendar_service()
        
        # Events are created with a start and end time.
        # For a reminder, we can make it a 30-minute event.
        event_body = {
            'summary': f"Reminder: {reminder.title}",
            'start': {
                'dateTime': reminder.remind_at.isoformat(),
                'timeZone': 'America/Chicago', # IMPORTANT: Should be user-configurable in a real app
            },
            'end': {
                'dateTime': (reminder.remind_at + timedelta(minutes=30)).isoformat(),
                'timeZone': 'America/Chicago',
            },
            'reminders': {
                'useDefault': True, # Use the user's default calendar notification settings
            },
        }
        
        created_event = calendar_service.events().insert(
            calendarId='primary', 
            body=event_body
        ).execute()
        
        print(f"--- Google Calendar event created successfully. Event ID: {created_event.get('id')} ---")

    except Exception as e:
        # If the calendar event fails, we still have the reminder saved locally.
        # A real app might have retry logic or mark the reminder as "sync failed".
        print(f"--- CRITICAL ERROR: Could not create Google Calendar event. {e} ---")
        # We don't raise an HTTPException here because the reminder was still created successfully in our system.
        # The frontend will still get a success response.
        pass

    return reminder

@router.get("/list", response_model=List[Reminder])
def get_all_reminders():
    """Retrieves a list of all reminders."""
    reminders = read_reminders()
    # Sort by reminder date, soonest first
    return reminders

@router.delete("/delete/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: str):
    """
    Deletes a reminder by its ID and also deletes the corresponding event from 
    Google Calendar by searching for its title on the correct date.
    """
    reminders = read_reminders()
    reminder_to_delete = next((r for r in reminders if r.id == reminder_id), None)

    if not reminder_to_delete:
        raise HTTPException(status_code=404, detail="Reminder not found")

    # --- UPDATED: New logic to find and delete the event by title and date ---
    try:
        print(f"--- Attempting to find and delete Google Calendar event for: '{reminder_to_delete.title}' ---")
        calendar_service = get_calendar_service()

        # Define the time range for the search (the entire day of the reminder)
        reminder_date = reminder_to_delete.remind_at.date()
        time_min = datetime.combine(reminder_date, time.min).isoformat() + 'Z' # Z for UTC
        time_max = datetime.combine(reminder_date, time.max).isoformat() + 'Z' # Z for UTC

        # List all events on that day
        events_result = calendar_service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # Find the specific event by matching the summary (title)
        event_to_delete_calendar = None # Use a different variable name to avoid shadowing
        expected_title = f"Reminder: {reminder_to_delete.title}"
        for event in events:
            if event.get('summary') == expected_title:
                event_to_delete_calendar = event
                break
        
        if event_to_delete_calendar:
            # If we found the event, delete it using its ID
            event_id = event_to_delete_calendar['id']
            print(f"--- Found matching event. Deleting event ID: {event_id} ---")
            calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
            print("--- Google Calendar event deleted successfully. ---")
        else:
            print(f"--- INFO: No matching Google Calendar event found for '{expected_title}' on {reminder_date}. It might have been deleted already. ---")

    except Exception as e:
        print(f"--- WARNING: An unexpected error occurred while deleting calendar event. {e} ---")

    # Finally, remove the reminder from our local database regardless of calendar success
    reminders.remove(reminder_to_delete)
    write_reminders(reminders)
    
    return