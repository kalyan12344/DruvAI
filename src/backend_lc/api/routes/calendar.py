# api/routes/calendar.py

from fastapi import APIRouter, HTTPException
from lc.calendar import get_all_events

router = APIRouter()

@router.get("/events")
def fetch_events_endpoint():
    """
    FastAPI endpoint to fetch all upcoming Google Calendar events.
    """
    try:
        all_events = get_all_events(max_results=250)
        return all_events
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch calendar events from Google."
        )