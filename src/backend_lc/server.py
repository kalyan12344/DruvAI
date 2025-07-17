# import os
# import json
# import firebase_admin
# from firebase_admin import credentials
# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.sessions import SessionMiddleware
# import firebase_admin
# from firebase_admin import credentials
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.triggers.cron import CronTrigger
# from lc.job_processor import process_and_cache_jobs
# import uvicorn
# from dotenv import load_dotenv

# load_dotenv()

# # --- Load Secrets from Environment ---
# # This key MUST be set in your deployment environment.
# SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY")

# # --- 1. Initialize Firebase FIRST (Robust Method) ---
# try:
#     # Get the credentials JSON string from the environment variable
#     creds_json_string = os.environ.get("FIREBASE_CREDENTIALS")

#     if not creds_json_string:
#         raise ValueError("FIREBASE_CREDENTIALS environment variable not set.")

#     # Parse the JSON string into a Python dictionary
#     creds_dict = json.loads(creds_json_string)
    
#     # Initialize the app with the credentials dictionary
#     cred = credentials.Certificate(creds_dict)
#     firebase_admin.initialize_app(cred)
#     print("✅ Firebase Admin SDK initialized successfully.")

# except Exception as e:
#     # This prevents the app from crashing on re-deployments
#     if 'already exists' in str(e).lower():
#         print("✅ Firebase Admin SDK already initialized.")
#     else:
#         print(f"🔥 CRITICAL: Failed to initialize Firebase Admin SDK: {e}")
#         exit()
# # --- 2. Import your routers AFTER Firebase is initialized ---
# from api.routes.agent import router as agent_router
# from api.routes.calendar import router as calendar_router
# from api.routes.webhooks import router as webhook_router
# from api.routes.resume import router as resume_router
# from api.routes.settings import router as settings_router
# from api.routes.jobs import router as jobs_router
# from api.routes.google_auth import router as google_auth_router
# from api.routes.gmail import router as gmail_router
# from api.routes.contacts import router as contact_router
# from api.routes.tasks import router as tasks_router
# from api.routes.remainders import router as remainders_router
# from api.routes.notes import router as notes_router
# from api.routes.news import router as news_router
# from api.routes.auth import router as auth_router

# # --- 3. Create the FastAPI app and add middleware ---
# app = FastAPI(title="Druv AI")

# if not SESSION_SECRET:
#     print("🔥 WARNING: SESSION_SECRET_KEY not set. Using a default insecure key for development.")
#     SESSION_SECRET = "a_default_insecure_secret_key"

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], # For production, it's best to restrict this to your frontend's domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# # The secret key is now loaded from the environment variable
# app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# scheduler = AsyncIOScheduler()

# # --- 4. Add your lifecycle events and routers ---
# @app.on_event("startup")
# async def startup_event():
#     scheduler.add_job(
#         process_and_cache_jobs,
#         trigger=CronTrigger(hour=6, minute=6),
#         id="daily_job_processing",
#         name="Daily Job Scraping and Caching",
#         replace_existing=True
#     )
#     scheduler.start()
#     print("APScheduler started.")

# @app.on_event("shutdown")
# async def shutdown_event():
#     scheduler.shutdown()
#     print("APScheduler shut down.")

# # --- 6. Add all your application routers ---
# app.include_router(auth_router, prefix="/api/auth", tags=["User Authentication"])
# app.include_router(agent_router, prefix="/agent", tags=["Agent"])
# app.include_router(calendar_router, prefix="/api/calendar", tags=["Calendar"])
# app.include_router(webhook_router, prefix="/api/webhooks", tags=["Webhooks"])
# app.include_router(resume_router, prefix="/api/resume", tags=["Resume"])
# app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
# app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
# app.include_router(google_auth_router, prefix="/api/google/auth", tags=["Google Auth"])
# app.include_router(notes_router, prefix="/api/notes", tags=["Notes"])
# # ... include all other routers as needed ...

# # --- 7. Health check endpoint for deployment environment ---
# @app.get("/api/ping", tags=["Health Check"])
# def ping():
#     """A simple health check endpoint to confirm the service is running."""
#     return {"status": "ok"}

# # --- This block is for local development only ---
# # It is NOT used when deploying with Gunicorn on Cloud Run.
# if __name__ == "__main__":
#     uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)


from fastapi import FastAPI

app = FastAPI(title="Druv AI - Test")

@app.get("/api/ping", tags=["Health Check"])
def ping():
    """A simple health check endpoint."""
    return {"status": "ok", "message": "Minimal test server is running!"}