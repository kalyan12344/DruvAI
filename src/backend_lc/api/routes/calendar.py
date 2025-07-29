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
            # If the user has no document, they are not connected
            return {"google": {"connected": False, "email": None}}
        
        user_data = user_doc.to_dict()
        
        # Read directly from the new 'calendars' map
        # Provide a default value if the map or key doesn't exist yet
        google_status = user_data.get("calendars", {}).get("google", {
            "connected": False,
            "email": None
        })
        
        return {"google": google_status}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))