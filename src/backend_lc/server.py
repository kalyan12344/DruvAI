# server.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os

# Import all of your routers
from api.routes.agent import router as agent_router
from api.routes.calendar import router as calendar_router
from api.routes.webhooks import router as webhook_router
from api.routes.resume import router as resume_router
from api.routes.settings import router as settings_router
from api.routes.jobs import router as jobs_router
from api.routes.google_auth import router as google_auth_router

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from lc.job_processor import process_and_cache_jobs
from api.routes.gmail import router as gmail_router 
from api.routes.contacts import router as contact_router
from api.routes.tasks import router as tasks_router
from api.routes.remainders import router as remainders_router
from api.routes.notes import router as notes_router



scheduler = AsyncIOScheduler()

app = FastAPI(title="Druv AI")

# --- Add the SessionMiddleware to enable request.session ---
# In production, this secret key should be loaded from an environment variable
# for security. e.g., os.environ.get("SECRET_KEY")
app.add_middleware(SessionMiddleware, secret_key="your_super_secret_random_string")

@app.on_event("startup")
async def startup_event():
    # Schedule the job to run every day at 6:00 AM server time
    scheduler.add_job(
        process_and_cache_jobs,
        trigger=CronTrigger(hour=6, minute=6),
        id="daily_job_processing",
        name="Daily Job Scraping and Caching",
        replace_existing=True
    )
    scheduler.start()
    print("APScheduler started. Daily job processing is scheduled for 6:00 AM.")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("APScheduler shut down.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add all the routers to your application
app.include_router(agent_router, prefix="/agent", tags=["Agent"])
app.include_router(calendar_router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(webhook_router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(resume_router, prefix="/api/resume", tags=["Resume"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
app.include_router(google_auth_router, prefix="/api/google/auth", tags=["Google Auth"])
app.include_router(calendar_router, prefix = "/api/calendars", tags = ["Calendar Status"])
app.include_router(gmail_router,prefix = "/api/gmail", tags = ["Gmail"])
app.include_router(contact_router,prefix = "/api/contacts", tags = ["Contacts"])
app.include_router(tasks_router,prefix = "/api/tasks", tags = ["Tasks"])
app.include_router(remainders_router, prefix = "/api/reminders", tags = ["Remainders"])
app.include_router(notes_router, prefix = "/api/notes", tags = ["Notes"])





if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)