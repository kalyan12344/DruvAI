import os
import json
import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

# --- Environment Variable Loading ---
# These MUST be set in your deployment environment (e.g., Cloud Run Variables & Secrets)
FIREBASE_CREDS_JSON = os.environ.get("FIREBASE_CREDENTIALS")
SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY")
CRON_API_KEY = os.environ.get("CRON_SECRET_API_KEY") # A secret key to protect the job endpoint


# --- 1. Initialize Firebase FIRST (Robust Method) ---
try:
    if not FIREBASE_CREDS_JSON:
        raise ValueError("CRITICAL: FIREBASE_CREDENTIALS environment variable is not set.")
    
    # Parse the JSON string from the env variable into a Python dict
    creds_dict = json.loads(FIREBASE_CREDS_JSON)
    
    # Initialize the app with the credentials dictionary (avoids writing a temp file)
    cred = credentials.Certificate(creds_dict)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK initialized successfully.")

except Exception as e:
    # This prevents the app from crashing on re-deployments where the app is already initialized
    if 'already exists' in str(e).lower():
        print("✅ Firebase Admin SDK already initialized.")
    else:
        print(f"🔥 CRITICAL: Failed to initialize Firebase Admin SDK: {e}")
        # In a real-world scenario, you might want the container to exit on critical failure
        # exit(1)

# --- 2. Import your routers AFTER Firebase is initialized ---
from api.routes.agent import router as agent_router
from api.routes.calendar import router as calendar_router
from api.routes.webhooks import router as webhook_router
from api.routes.resume import router as resume_router
from api.routes.settings import router as settings_router
from api.routes.jobs import router as jobs_router
from api.routes.google_auth import router as google_auth_router
from api.routes.gmail import router as gmail_router
from api.routes.contacts import router as contact_router
from api.routes.tasks import router as tasks_router
from api.routes.remainders import router as remainders_router
from api.routes.notes import router as notes_router
from api.routes.news import router as news_router
from api.routes.auth import router as auth_router

# --- 3. Create the FastAPI app and add middleware ---
app = FastAPI(title="Druv AI")

# Use the secret key from an environment variable for security
if not SESSION_SECRET:
    print("🔥 WARNING: SESSION_SECRET_KEY not set. Using a default insecure key for development.")
    SESSION_SECRET = "a_default_insecure_secret_key"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, it's best to restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# --- 4. Define a function to protect your scheduled job endpoint ---
async def verify_api_key(request: Request):
    """A dependency to verify a secret API key in the request header."""
    api_key = request.headers.get("x-api-key")
    if not CRON_API_KEY or api_key != CRON_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key for cron job.")

# --- 5. Create an endpoint for your scheduled job ---
# This replaces the unreliable `apscheduler` for serverless environments.
# Configure a service like Google Cloud Scheduler to send a POST request to this
# URL at your desired time, including the secret API key in the 'x-api-key' header.
@app.post("/api/tasks/run-daily-job", tags=["Scheduled Tasks"], dependencies=[Depends(verify_api_key)])
async def trigger_process_and_cache_jobs():
    """
    This endpoint is triggered by an external cron service to run the daily job processing task.
    It is protected by a secret API key.
    """
    from lc.job_processor import process_and_cache_jobs
    try:
        print("Scheduler triggered: Starting daily job processing...")
        await process_and_cache_jobs() # Run your job function
        print("✅ Daily job processing finished successfully.")
        return {"status": "success", "message": "Job processing triggered successfully."}
    except Exception as e:
        print(f"🔥 Daily job processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job processing failed: {e}")

# --- 6. Add all your application routers ---
app.include_router(auth_router, prefix="/api/auth", tags=["User Authentication"])
app.include_router(agent_router, prefix="/agent", tags=["Agent"])
app.include_router(calendar_router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(webhook_router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(resume_router, prefix="/api/resume", tags=["Resume"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
app.include_router(google_auth_router, prefix="/api/google/auth", tags=["Google Auth"])
app.include_router(notes_router, prefix="/api/notes", tags=["Notes"])
# ... include all other routers as needed ...

# --- 7. Health check endpoint for deployment environment ---
@app.get("/api/ping", tags=["Health Check"])
def ping():
    """A simple health check endpoint to confirm the service is running."""
    return {"status": "ok"}

# --- This block is for local development only ---
# It is NOT used when deploying with Gunicorn on Cloud Run.
if __name__ == "__main__":
    # When running locally, you'll need to set the required environment variables
    # in your shell or use a .env file with a library like `python-dotenv`.
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)