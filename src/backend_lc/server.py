import uvicorn
import firebase_admin
import os
import json
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from firebase_admin import credentials

# --- 1. Initialize Firebase FIRST ---
# This is the most critical step. It must run before any other
# code in your application tries to access Firebase services.
try:
    # For deploying to Google Cloud Run, it's best practice to store your
    # credentials as a secret environment variable.
    creds_json_str = os.getenv("FIREBASE_CREDENTIALS_JSON")
    
    if creds_json_str:
        # If the environment variable is found, load credentials from it
        creds_dict = json.loads(creds_json_str)
        cred = credentials.Certificate(creds_dict)
    else:
        # Fallback for local development: use the JSON file
        cred = credentials.Certificate("firebase-service-account.json")

    # Get the storage bucket from an environment variable for security
    storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")
    if not storage_bucket:
        raise ValueError("FIREBASE_STORAGE_BUCKET environment variable not set.")

    firebase_admin.initialize_app(cred, {'storageBucket': storage_bucket})
    print("✅ Firebase Admin SDK initialized successfully.")

except FileNotFoundError:
    print("🔥 CRITICAL: 'firebase-service-account.json' not found for local development.")
    exit()
except Exception as e:
    print(f"🔥 CRITICAL: Failed to initialize Firebase Admin SDK: {e}")
    exit()


# --- 2. Import your routers AFTER Firebase is initialized ---
from api.routes import (
    agent, auth, calendar, contacts, gmail,
    google_auth, jobs, news, notes,
    remainders, resume
)
# Note: The user's file list did not include 'settings' or 'webhooks',
# so they are commented out to prevent import errors.
# from api.routes.settings import router as settings_router
# from api.routes.webhooks import router as webhook_router


# --- 3. Create the FastAPI app and add middleware ---
app = FastAPI(
    title="DruvAI API v2 (Multi-User)",
    description="API for all DruvAI services, now with user-specific data powered by Firebase."
)

# Add CORS middleware to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Best to restrict this to your actual frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add session middleware - required for the Google OAuth state management
app.add_middleware(SessionMiddleware, secret_key="your-super-strong-and-secret-key-here")


# --- 4. Include All API Routers ---
app.include_router(auth.router, prefix="/api/auth", tags=["User Authentication"])
app.include_router(google_auth.router, prefix="/api/google/auth", tags=["Google Service Connection"])
app.include_router(agent.router, prefix="/api/agent", tags=["Smart Agent"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["Contacts"])
app.include_router(gmail.router, prefix="/api/gmail", tags=["Gmail"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
app.include_router(remainders.router, prefix="/api/reminders", tags=["Reminders"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
# app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
# app.include_router(webhook_router, prefix="/api/webhooks", tags=["Webhooks"])


# --- 5. Add a Health Check Endpoint ---
@app.get("/api/ping")
def ping():
    """A simple endpoint to verify that the server is running."""
    return {"status": "ok"}

# The uvicorn.run command is removed.
# For deployment, the server will be started by the CMD instruction in your Dockerfile.
# For local development, run: uvicorn server:app --host 0.0.0.0 --port 8000 --reload
