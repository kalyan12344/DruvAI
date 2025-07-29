# api/routes/remainders.py
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from firebase_admin import firestore

from core.google_auth import get_calendar_service
from api.routes.auth import User, get_current_user

router = APIRouter()

# --- Pydantic Model ---
class Reminder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    remind_at: datetime
    status: str = "Pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- API Endpoints using Firestore ---

@router.post("/add", response_model=Reminder, status_code=status.HTTP_201_CREATED)
def create_reminder(reminder: Reminder, current_user: User = Depends(get_current_user)):
    """
    Creates a new reminder in Firestore under the user's document AND adds it to their Google Calendar.
    """
    db = firestore.client()
    try:
        # Save reminder to the user's 'reminders' subcollection in Firestore
        reminder_ref = db.collection('users').document(current_user.uid).collection('reminders').document(reminder.id)
        reminder_ref.set(reminder.dict())
        print(f"--- Reminder '{reminder.title}' saved to Firestore for user {current_user.uid}. ---")

        # Add the corresponding event to Google Calendar
        calendar_service = get_calendar_service(user_id=current_user.uid)
        event_body = {
            'summary': f"Reminder: {reminder.title}",
            'start': {'dateTime': reminder.remind_at.isoformat(), 'timeZone': 'America/Chicago'},
            'end': {'dateTime': (reminder.remind_at + timedelta(minutes=30)).isoformat(), 'timeZone': 'America/Chicago'},
            'reminders': {'useDefault': True},
        }
        calendar_service.events().insert(calendarId='primary', body=event_body).execute()
        print(f"--- Google Calendar event created successfully. ---")

    except Exception as e:
        print(f"--- CRITICAL ERROR: {e} ---")
        raise HTTPException(status_code=500, detail=str(e))

    return reminder

@router.get("/list", response_model=List[Reminder])
def get_all_reminders(current_user: User = Depends(get_current_user)):
    """Retrieves a list of all reminders for the authenticated user from Firestore."""
    db = firestore.client()
    reminders_ref = db.collection('users').document(current_user.uid).collection('reminders').order_by("remind_at").stream()
    
    reminders = [doc.to_dict() for doc in reminders_ref]
    return reminders

@router.delete("/delete/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: str, current_user: User = Depends(get_current_user)):
    """Deletes a reminder from Firestore and also from Google Calendar."""
    db = firestore.client()
    reminder_ref = db.collection('users').document(current_user.uid).collection('reminders').document(reminder_id)
    
    reminder_doc = reminder_ref.get()
    if not reminder_doc.exists:
        raise HTTPException(status_code=404, detail="Reminder not found in Firestore")

    reminder_to_delete = Reminder(**reminder_doc.to_dict())
    
    try:
        # Delete from Google Calendar first
        calendar_service = get_calendar_service(user_id=current_user.uid)
        
        time_min = reminder_to_delete.remind_at.date().isoformat() + "T00:00:00Z"
        time_max = reminder_to_delete.remind_at.date().isoformat() + "T23:59:59Z"
        
        events_result = calendar_service.events().list(calendarId='primary', timeMin=time_min, timeMax=time_max, singleEvents=True).execute()
        events = events_result.get('items', [])
        
        expected_title = f"Reminder: {reminder_to_delete.title}"
        for event in events:
            if event.get('summary') == expected_title:
                calendar_service.events().delete(calendarId='primary', eventId=event['id']).execute()
                print(f"--- Google Calendar event deleted successfully. ---")
                break
        
        # Finally, delete from Firestore
        reminder_ref.delete()

    except Exception as e:
        print(f"--- WARNING: An unexpected error occurred during deletion. {e} ---")
        # Still attempt to delete from Firestore even if calendar fails
        reminder_ref.delete()
        raise HTTPException(status_code=500, detail=f"Error during deletion process: {e}")