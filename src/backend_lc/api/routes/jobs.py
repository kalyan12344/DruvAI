# In api/routes/jobs.py

import os
import json
from fastapi import APIRouter
from datetime import date

# (keep other necessary imports)

router = APIRouter()
CACHE_DIR = "cache"

# You can keep _read_settings_db if you still need it for the toggle
def _read_settings_db():
    try:
        with open("db.json", 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"jobs_feature_enabled": False}

@router.get("/today")
async def get_todays_jobs():
    print("🔍 Fetching today's jobs...")
    settings = _read_settings_db()
    if not settings.get("jobs_feature_enabled"):
        return []

    today_str = date.today().isoformat()
    cache_file = os.path.join(CACHE_DIR, f"todays_jobs_{today_str}.json")
    print(f"🔍 Checking cache for today's jobs: {cache_file}")
    # This function should ONLY check the cache.
    # The background task is responsible for creating this file.
    if os.path.exists(cache_file):
        print("✅ Serving jobs from today's cache.")
        with open(cache_file, 'r') as f:
            return json.load(f)
    else:
        # If no cache exists, it means the background job hasn't run or is in progress.
        # Return an empty list to avoid errors on the frontend.
        print("🟡 No job cache found for today. The background job may not have run yet.")
        return []