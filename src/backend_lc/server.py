# server.py (Updated)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all of your routers
from api.routes.agent import router as agent_router
from api.routes.calendar import router as calendar_router 
from api.routes.webhooks import router as webhook_router # <-- NEW IMPORT

app = FastAPI(title="Druv AI")

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
app.include_router(webhook_router, prefix="/api/webhooks", tags=["Webhooks"]) # <-- NEW LINE

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)