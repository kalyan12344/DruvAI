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
        print("userID",current_user)
        return get_all_events(user_id=current_user.uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_connection_status(current_user: User = Depends(get_current_user)):
    """Checks Firestore for the user's calendar connection status."""
    try:
        db = firestore.client()
        user_doc = db.collection('users').document(current_user.uid).get()
        if not user_doc.exists:
            return {"google": {"connected": False}}
        
        user_data = user_doc.to_dict()
        creds = user_data.get("google_credentials", {}).get("calendar_token")
        
        if creds:
            return {"google": {"connected": True, "user_email": user_data.get("email")}}
        return {"google": {"connected": False}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))