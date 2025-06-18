# api/routes/calendar.py

from fastapi import APIRouter, HTTPException
from lc.calendar import get_all_events
import json

router = APIRouter()

@router.get("/events")
def fetch_events_endpoint():
    """
    FastAPI endpoint to fetch all upcoming Google Calendar events.
    """
    try:
        with open("db.json", 'r') as f:
            db_data = json.load(f)
            is_google_connected = db_data.get("connected_calendars", {}).get("google", {}).get("connected", False) # 
        if(is_google_connected):
            all_events = get_all_events(max_results=250)
            return all_events
        else:
            return "connect google calender to fetch events"
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch calendar events from Google."
        )


@router.get("/status")
async def get_calendar_connection_status():
    with open("db.json", 'r') as f:
        db_data = json.load(f)
        print(db_data.get("connected_calendars.google", {}))
    return db_data.get("connected_calendars", {})