# In api/routes/jobs.py

import os
import json
from fastapi import APIRouter
from fastapi.responses import Response # Import Response
from datetime import date

# Import the custom renderer
from api.routes.utils import render_json_with_nan_handling

router = APIRouter()
CACHE_DIR = "cache"

def _read_settings_db():
    try:
        with open("db.json", 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"jobs_feature_enabled": False}

@router.get("/today") # Updated route path for clarity
async def get_todays_jobs():
    print("🔍 Fetching today's jobs...")
    settings = _read_settings_db()
    if not settings.get("jobs_feature_enabled"):
        return []

    today_str = date.today().isoformat()
    cache_file = os.path.join(CACHE_DIR, f"todays_jobs_{today_str}.json")
    
    print(f"🔍 Checking cache for today's jobs: {cache_file}")
    if os.path.exists(cache_file):
        print("✅ Serving jobs from today's cache.")
        with open(cache_file, 'r') as f:
            job_data = json.load(f)
        
        # --- THIS IS THE FIX ---
        # 1. Render the Python object to a JSON string using our custom handler.
        json_string = render_json_with_nan_handling(job_data)
        
        # 2. Return it as a FastAPI Response with the correct media type.
        # This bypasses FastAPI's default encoder and prevents the crash.
        return Response(content=json_string, media_type="application/json")
    else:
        print("🟡 No job cache found for today.")
        return []
