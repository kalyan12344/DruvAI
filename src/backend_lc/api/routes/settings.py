# api/routes/settings.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from firebase_admin import firestore

router = APIRouter()

# --- Pydantic Model ---
class SettingsToggle(BaseModel):
    enabled: bool

# --- Firestore Document Reference ---
def get_settings_doc():
    db = firestore.client()
    # Use a predictable document for app-wide settings
    return db.collection('config').document('features')

# --- API Endpoints ---
@router.get("/jobs-toggle-status")
async def get_jobs_toggle_status():
    """Gets the current status of the AI Jobs feature toggle from Firestore."""
    try:
        doc = get_settings_doc().get()
        if doc.exists:
            return {"enabled": doc.to_dict().get("jobs_feature_enabled", False)}
        # Default to false if the document doesn't exist yet
        return {"enabled": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs-toggle")
async def set_jobs_toggle(toggle: SettingsToggle):
    """Sets the status of the AI Jobs feature toggle in Firestore."""
    try:
        get_settings_doc().set({
            "jobs_feature_enabled": toggle.enabled
        }, merge=True) # Use merge=True to create or update
        return {"message": f"Jobs feature set to {toggle.enabled}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))