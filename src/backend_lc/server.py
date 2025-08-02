#server.py
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

#test 1 working

# from fastapi import FastAPI

# app = FastAPI(title="Druv AI - Test")

# @app.get("/api/ping", tags=["Health Check"])
# def ping():
#     """A simple health check endpoint."""
#     return {"status": "ok", "message": "Minimal test server is running!"}

#test 2 working

# import os
# from fastapi import FastAPI
# from starlette.middleware.sessions import SessionMiddleware
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv

# load_dotenv()

# SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY")

# app = FastAPI(title="Druv AI")

# if not SESSION_SECRET:
#     raise ValueError("ERROR: SESSION_SECRET_KEY environment variable is not set.")

# app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
# app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# @app.get("/api/ping", tags=["Health Check"])
# def ping():
#     return {"status": "ok", "message": "Step 2: Middleware is working!"} 

#test 3 ------------------------------------------------------------working
# import os
# import json
# from fastapi import FastAPI
# from starlette.middleware.sessions import SessionMiddleware
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# import firebase_admin
# from firebase_admin import credentials

# load_dotenv()

# SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY")
# FIREBASE_CREDS_JSON = os.environ.get("FIREBASE_CREDENTIALS")

# # --- Firebase Initialization ---
# try:
#     if not FIREBASE_CREDS_JSON:
#         raise ValueError("ERROR: FIREBASE_CREDENTIALS environment variable is not set.")
    
#     creds_dict = json.loads(FIREBASE_CREDS_JSON)
#     cred = credentials.Certificate(creds_dict)
#     if not firebase_admin._apps:
#         firebase_admin.initialize_app(cred)
#     print("✅ Firebase initialized.")
# except Exception as e:
#     print(f"🔥 Firebase initialization failed: {e}")
#     raise

# # --- FastAPI App ---
# app = FastAPI(title="Druv AI")
# app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
# app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# @app.get("/api/ping", tags=["Health Check"])
# def ping():
#     return {"status": "ok", "message": "Step 3: Firebase is working!"}


#test 4 final ------------------------------------------------------------ not working 
# import os
# import json
# import firebase_admin
# from firebase_admin import credentials
# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.sessions import SessionMiddleware
# from starlette.requests import Request
# from dotenv import load_dotenv

# # Load .env file for local development
# load_dotenv()

# # --- Environment Variable Loading ---
# # These MUST be set in your Cloud Run service configuration.
# FIREBASE_CREDS_JSON = os.environ.get("FIREBASE_CREDENTIALS")
# SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY")
# CRON_API_KEY = os.environ.get("CRON_SECRET_API_KEY") # A secret key to protect the job endpoint


# # --- 1. Initialize Firebase FIRST (Robust Method) ---
# try:
#     if not FIREBASE_CREDS_JSON:
#         raise ValueError("CRITICAL: FIREBASE_CREDENTIALS environment variable is not set.")
    
#     # Parse the JSON string from the env variable into a Python dict
#     creds_dict = json.loads(FIREBASE_CREDS_JSON)
    
#     # Initialize the app with the credentials dictionary (avoids writing a temp file)
#     cred = credentials.Certificate(creds_dict)
#     if not firebase_admin._apps:
#         firebase_admin.initialize_app(cred)
#     print("✅ Firebase Admin SDK initialized successfully.")

# except Exception as e:
#     print(f"🔥 CRITICAL: Firebase initialization failed: {e}")
#     # Re-raise the exception to make the startup failure clear in the logs
#     raise


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

# # Use the secret key from an environment variable for security
# if not SESSION_SECRET:
#     print("🔥 WARNING: SESSION_SECRET_KEY not set. Using a default insecure key for development.")
#     SESSION_SECRET = "a_default_insecure_secret_key"

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # For production, it's best to restrict this to your frontend's domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# # --- 4. Define a function to protect your scheduled job endpoint ---
# async def verify_api_key(request: Request):
#     """A dependency to verify a secret API key in the request header."""
#     api_key = request.headers.get("x-api-key")
#     if not CRON_API_KEY or api_key != CRON_API_KEY:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key for cron job.")

# # --- 5. Create an endpoint for your scheduled job ---
# @app.post("/api/tasks/run-daily-job", tags=["Scheduled Tasks"], dependencies=[Depends(verify_api_key)])
# async def trigger_process_and_cache_jobs():
#     """
#     This endpoint is triggered by an external cron service (like Google Cloud Scheduler)
#     to run the daily job processing task. It is protected by a secret API key.
#     """
#     from lc.job_processor import process_and_cache_jobs
#     try:
#         print("Scheduler triggered: Starting daily job processing...")
#         await process_and_cache_jobs() # Run your job function
#         print("✅ Daily job processing finished successfully.")
#         return {"status": "success", "message": "Job processing triggered successfully."}
#     except Exception as e:
#         print(f"🔥 Daily job processing failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Job processing failed: {e}")

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
# app.include_router(gmail_router, prefix="/api/gmail", tags=["Gmail"])
# app.include_router(contact_router, prefix="/api/contacts", tags=["Contacts"])
# app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
# app.include_router(remainders_router, prefix="/api/remainders", tags=["Remainders"])
# app.include_router(news_router, prefix="/api/news", tags=["News"])

# # --- 7. Health check endpoint for deployment environment ---
# @app.get("/api/ping", tags=["Health Check"])
# def ping():
#     """A simple health check endpoint to confirm the service is running."""
#     return {"status": "ok"}

# # --- This block is for local development only ---
# # It is NOT used when deploying with Gunicorn on Cloud Run.
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)


#test 5 firebase ------------------------------------------------------------ working
# import os
# import json
# from fastapi import FastAPI
# from dotenv import load_dotenv

# load_dotenv()

# app = FastAPI(title="Firebase Credentials Test")

# @app.get("/")
# def check_firebase_credentials():
#     """
#     This endpoint tests if the FIREBASE_CREDENTIALS environment variable
#     can be successfully loaded and parsed as JSON.
#     """
#     creds_json_string = os.environ.get("FIREBASE_CREDENTIALS")

#     if not creds_json_string:
#         return {
#             "status": "ERROR",
#             "message": "The FIREBASE_CREDENTIALS environment variable is not set."
#         }
    
#     try:
#         # Try to parse the JSON string
#         creds_dict = json.loads(creds_json_string)
#         # Check if it looks like a service account
#         if isinstance(creds_dict, dict) and creds_dict.get("type") == "service_account":
#             return {
#                 "status": "SUCCESS",
#                 "message": "FIREBASE_CREDENTIALS variable was found and is valid JSON."
#             }
#         else:
#             return {
#                 "status": "ERROR",
#                 "message": "FIREBASE_CREDENTIALS value is not a valid service account JSON object."
#             }
#     except json.JSONDecodeError as e:
#         # If parsing fails, return the specific error
#         return {
#             "status": "ERROR",
#             "message": "Failed to parse FIREBASE_CREDENTIALS as JSON.",
#             "json_error": str(e)
#         }



# #test 6 ------------------------------------------------------------ not working
# import os
# import json
# from fastapi import FastAPI
# from starlette.middleware.sessions import SessionMiddleware
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# import firebase_admin
# from firebase_admin import credentials

# load_dotenv()

# # --- All the startup code we've confirmed is working ---
# SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY")
# FIREBASE_CREDS_JSON = os.environ.get("FIREBASE_CREDENTIALS")

# try:
#     if not FIREBASE_CREDS_JSON:
#         raise ValueError("ERROR: FIREBASE_CREDENTIALS environment variable is not set.")
    
#     creds_dict = json.loads(FIREBASE_CREDS_JSON)
#     cred = credentials.Certificate(creds_dict)
#     if not firebase_admin._apps:
#         firebase_admin.initialize_app(cred)
#     print("✅ Firebase initialized.")
# except Exception as e:
#     print(f"🔥 Firebase initialization failed: {e}")
#     raise

# app = FastAPI(title="Druv AI")
# app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
# app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# # Health check endpoint
# @app.get("/api/ping", tags=["Health Check"])
# def ping():
#     return {"status": "ok", "message": "Full application is running!"}


# test 7 ------------------------------------------------------------ 
import os
import json
import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from dotenv import load_dotenv

import logging # Add this import
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting server.py execution...")

load_dotenv()

logger.info("Loading environment variables...")
FIREBASE_CREDS_JSON = os.environ.get("FIREBASE_CREDENTIALS")
SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY")
CRON_API_KEY = os.environ.get("CRON_SECRET_API_KEY")

if not SESSION_SECRET:
    logger.warning("SESSION_SECRET_KEY not set. Using a default insecure key for development. This is a security risk in production!")
    SESSION_SECRET = "a_default_insecure_secret_key"

logger.info("Environment variables loaded.")

# --- Initialize Firebase FIRST (Robust Method) ---
logger.info("Attempting to initialize Firebase Admin SDK...")
try:
    if not FIREBASE_CREDS_JSON:
        logger.critical("FIREBASE_CREDENTIALS environment variable is not set. Exiting.")
        exit(1)

    logger.info("FIREBASE_CREDENTIALS found. Attempting to parse JSON...")
    creds_dict = json.loads(FIREBASE_CREDS_JSON)
    logger.info("JSON parsed successfully.")

    cred = credentials.Certificate(creds_dict)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase Admin SDK initialized successfully.")
    else:
        logger.info("Firebase Admin SDK already initialized.")

except json.JSONDecodeError as e:
    logger.critical(f" CRITICAL: Failed to decode FIREBASE_CREDENTIALS. Invalid JSON format: {e}. Exiting.")
    exit(1)
except Exception as e:
    logger.critical(f" CRITICAL: An unexpected error occurred during Firebase initialization: {e}. Exiting.")
    exit(1)

logger.info("Firebase initialization block completed.")

# --- Import your routers AFTER Firebase is initialized ---
logger.info("Importing API routers...")
try:
    # UNCOMMENT ALL YOUR ACTUAL ROUTER IMPORTS HERE:
    from api.routes.agent import router as agent_router
    from api.routes.calendar import router as calendar_router
    from api.routes.webhooks import router as webhook_router
    # from api.routes.resume import router as resume_router
    from api.routes.settings import router as settings_router
    # from api.routes.jobs import router as jobs_router
    from api.routes.google_auth import router as google_auth_router
    from api.routes.gmail import router as gmail_router
    from api.routes.contacts import router as contact_router
    from api.routes.tasks import router as tasks_router
    from api.routes.remainders import router as remainders_router
    from api.routes.notes import router as notes_router
    from api.routes.news import router as news_router
    from api.routes.auth import router as auth_router

    logger.info("API routers imported successfully.")
except ImportError as e:
    logger.critical(f" CRITICAL: Failed to import one or more routers: {e}. Check your 'api.routes' directory and module names. Exiting.")
    exit(1)
except Exception as e:
    logger.critical(f" CRITICAL: An unexpected error occurred during router import: {e}. Exiting.")
    exit(1)


logger.info("Creating FastAPI app instance and adding middleware...")
app = FastAPI(title="Druv AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
logger.info("FastAPI app created and middleware added.")

async def verify_api_key(request: Request):
    api_key = request.headers.get("x-api-key")
    if not CRON_API_KEY or api_key != CRON_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key for cron job.")

@app.post("/api/tasks/run-daily-job", tags=["Scheduled Tasks"], dependencies=[Depends(verify_api_key)])
async def trigger_process_and_cache_jobs():
    from lc.job_processor import process_and_cache_jobs
    try:
        logger.info("Scheduler triggered: Starting daily job processing...")
        await process_and_cache_jobs()
        logger.info(" Daily job processing finished successfully.")
        return {"status": "success", "message": "Job processing triggered successfully."}
    except Exception as e:
        logger.error(f" Daily job processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job processing failed: {e}")

# --- Add all your application routers ---
logger.info("Including application routers...")
app.include_router(auth_router, prefix="/api/auth", tags=["User Authentication"])
app.include_router(agent_router, prefix="/agent", tags=["Agent"])
app.include_router(calendar_router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(webhook_router, prefix="/api/webhooks", tags=["Webhooks"])
# app.include_router(resume_router, prefix="/api/resume", tags=["Resume"])
# app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
app.include_router(google_auth_router, prefix="/api/google/auth", tags=["Google Auth"])
app.include_router(gmail_router, prefix="/api/gmail", tags=["Gmail"])
app.include_router(contact_router, prefix="/api/contacts", tags=["Contacts"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(remainders_router, prefix="/api/remainders", tags=["Remainders"])
app.include_router(notes_router, prefix="/api/notes", tags=["Notes"])
app.include_router(news_router, prefix="/api/news", tags=["News"])
logger.info("All routers included.")

# --- Health check endpoint for deployment environment ---
@app.get("/api/ping", tags=["Health Check"])
def ping():
    logger.info("Ping endpoint hit.")
    # Change the message to reflect the full app is running
    return {"status": "ok", "message": "Step 6: Full application is running!"}

logger.info("Server.py execution complete. Application is ready.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)