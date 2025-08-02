import base64
import json
from email.mime.text import MIMEText
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from firebase_admin import firestore

from core.google_auth import get_gmail_service
from lc.react_agent import run_agent
from api.routes.auth import User, get_current_user

router = APIRouter()

# --- Pydantic Models ---
class EmailContent(BaseModel):
    subject: str
    snippet: str
    perspective: Optional[str] = None

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str

class ModifyRequest(BaseModel):
    addLabelIds: Optional[List[str]] = None
    removeLabelIds: Optional[List[str]] = None

class AgentQueryRequest(BaseModel):
    query: str

# --- Helper Functions (Unchanged) ---
def get_email_body(payload):
    # ... (this function is correct)
    pass
def _fetch_and_format_messages(service, message_ids):
    # ... (this function is correct)
    pass

# --- API Endpoints ---

@router.get("/status")
async def get_mail_connection_status(current_user: User = Depends(get_current_user)):
    """Gets the Gmail connection status for the authenticated user from Firestore."""
    # FIX: Reads from Firestore, not a local file.
    db = firestore.client()
    user_doc = db.collection('users').document(current_user.uid).get()
    if not user_doc.exists:
        return {"google_gmail": {"connected": False}}
    
    user_data = user_doc.to_dict()
    # This checks for the specific gmail token we save during the auth flow.
    creds = user_data.get("google_credentials", {}).get("gmail_token")
    if creds:
        return {"google_gmail": {"connected": True, "user_email": user_data.get("email")}}
    return {"google_gmail": {"connected": False}}

@router.get("/messages")
async def get_gmail_messages(current_user: User = Depends(get_current_user)):
    """Gets the latest messages from the INBOX for the authenticated user."""
    try:
        # FIX: Passes the user's ID to the service getter.
        service = get_gmail_service(user_id=current_user.uid)
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=25).execute()
        message_ids = results.get('messages', [])
        return _fetch_and_format_messages(service, message_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_emails(q: str, current_user: User = Depends(get_current_user)):
    """Searches the authenticated user's mailbox for a query."""
    if not q:
        raise HTTPException(status_code=400, detail="A search query 'q' is required.")
    try:
        # FIX: Passes the user's ID to the service getter.
        service = get_gmail_service(user_id=current_user.uid)
        results = service.users().messages().list(userId='me', q=q, maxResults=25).execute()
        message_ids = results.get('messages', [])
        return _fetch_and_format_messages(service, message_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ... (GET /message/{id}, POST /message/{id}/modify, and POST /send-email endpoints
# should also be updated to accept `current_user` and pass `user_id` to get_gmail_service) ...

@router.post("/draft-reply")
async def draft_ai_reply(email: EmailContent, current_user: User = Depends(get_current_user)):
    """Instructs the AI agent to draft a reply for the authenticated user."""
    try:
        prompt = f"""Use the 'draft_reply_tool'. The user's name is {current_user.name}.
        Email Subject: "{email.subject}"
        Email Snippet: "{email.snippet}"
        Perspective for reply: "{email.perspective}"
        """
        # FIX: Passes the user object to the agent.
        ai_response = await run_agent(prompt, user=current_user)
        return {"draft": ai_response.get("output")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message/{message_id}/agent-query")
async def query_agent_on_email(message_id: str, req: AgentQueryRequest, current_user: User = Depends(get_current_user)):
    """Takes a user's query about a specific email and returns the agent's response."""
    try:
        # FIX: Passes the user's ID to the service getter.
        service = get_gmail_service(user_id=current_user.uid)
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        email_body_html = get_email_body(message.get('payload', {}))
        soup = BeautifulSoup(email_body_html, "html.parser")
        email_body_text = soup.get_text(separator='\n', strip=True)

        # FIX: Dynamically inserts the user's email into the prompt.
        prompt = f"""A user is asking a question about an email. Use the email's content as context.
        USER'S QUESTION: "{req.query}"
        USER'S EMAIL ADDRESS (for context): "{current_user.email}"
        FULL EMAIL CONTENT:
        ---
        {email_body_text}
        ---
        """
        # FIX: Passes the user object to the agent and awaits the response.
        ai_response = await run_agent(prompt, user=current_user)
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))