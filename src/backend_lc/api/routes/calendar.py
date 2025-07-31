#api/routes/calendar.py
from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import firestore
from lc.calendar import get_all_events
from api.routes.auth import User, get_current_user

router = APIRouter()

@router.get("/events")
def fetch_events_endpoint(current_user: User = Depends(get_current_user)):
    """Fetches calendar events for the authenticated user."""
    try:
        # Pass the authenticated user's ID to the logic function
        return get_all_events(user_id=current_user.uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/status")
def get_connection_status(current_user: User = Depends(get_current_user)):
    """Checks Firestore for the user's simplified calendar connection status."""
    try:
        db = firestore.client()
        user_doc = db.collection('users').document(current_user.uid).get()

        if not user_doc.exists:
            return {"google": {"connected": False, "email": None}}
        
        user_data = user_doc.to_dict()
        
        # FIX: Look for "calendar" to match your Firestore data structure
        google_status = user_data.get("calendars", {}).get("calendar", {
            "connected": False,
            "email": None
        })
        
        # The key in the final response should still be "google" for the frontend
        return {"google": google_status}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))