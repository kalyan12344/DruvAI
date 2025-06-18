# api/routes/settings.py

import json
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

router = APIRouter()
DB_FILE = "db.json"

# --- Pydantic Model for Request Body ---
class SettingsToggle(BaseModel):
    enabled: bool

# --- Helper Functions for DB ---
def read_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return a default state if file is missing or corrupt
        return {"jobs_feature_enabled": False}

def write_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# --- API Endpoints ---
@router.get("/jobs-toggle-status")
async def get_jobs_toggle_status():
    """Gets the current status of the AI Jobs feature toggle."""
    db_data = read_db()
    return {"enabled": db_data.get("jobs_feature_enabled", False)}

@router.post("/jobs-toggle")
async def set_jobs_toggle(toggle: SettingsToggle):
    """Sets the status of the AI Jobs feature toggle."""
    db_data = read_db()
    db_data["jobs_feature_enabled"] = toggle.enabled
    write_db(db_data)
    return {"message": f"Jobs feature set to {toggle.enabled}"}