import base64
import json
from email.mime.text import MIMEText
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from firebase_admin import firestore

# FIX: Added imports for authentication and the User model
from api.routes.auth import User, get_current_user
from core.google_auth import get_gmail_service
from lc.react_agent import run_agent

router = APIRouter()

# --- Pydantic Models (Unchanged) ---
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
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/html':
                data = part['body'].get('data', '')
                return base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
            body = get_email_body(part)
            if body:
                return body
    elif 'body' in payload and payload['body'].get('data'):
        data = payload['body']['data']
        return base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
    return ""

def _fetch_and_format_messages(service, message_ids):
    if not message_ids:
        return []
    formatted_messages = []
    for msg_summary in message_ids:
        msg_id = msg_summary['id']
        message = service.users().messages().get(userId='me', id=msg_id, format='metadata').execute()
        headers = message.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'No Sender')
        formatted_messages.append({
            'id': message['id'], 'threadId': message['threadId'],
            'snippet': message.get('snippet', ''), 'subject': subject,
            'from': sender.split('<')[0].strip(),
        })
    return formatted_messages

# --- API Endpoints ---

@router.get("/status")
async def get_mail_connection_status(current_user: User = Depends(get_current_user)):
    """Gets the Gmail connection status for the authenticated user from Firestore."""
    db = firestore.client()
    user_doc = db.collection('users').document(current_user.uid).get()
    if not user_doc.exists:
        return {"google_gmail": {"connected": False}}
    user_data = user_doc.to_dict()
    creds = user_data.get("google_credentials", {}).get("gmail_token")
    if creds:
        return {"google_gmail": {"connected": True, "user_email": user_data.get("email")}}
    return {"google_gmail": {"connected": False}}

@router.get("/messages")
async def get_gmail_messages(current_user: User = Depends(get_current_user)):
    """Gets the latest messages from the INBOX for the authenticated user."""
    try:
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
        service = get_gmail_service(user_id=current_user.uid)
        results = service.users().messages().list(userId='me', q=q, maxResults=25).execute()
        message_ids = results.get('messages', [])
        return _fetch_and_format_messages(service, message_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/message/{message_id}")
async def get_single_email(message_id: str, current_user: User = Depends(get_current_user)):
    """Fetches the full content of a single email for the authenticated user."""
    try:
        service = get_gmail_service(user_id=current_user.uid)
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'No Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        body_html = get_email_body(payload)
        return {'id': message['id'], 'subject': subject, 'from': sender, 'date': date, 'snippet': message.get('snippet', ''), 'body': body_html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message/{message_id}/modify")
async def modify_email(message_id: str, req: ModifyRequest, current_user: User = Depends(get_current_user)):
    """Modifies an email's labels for the authenticated user."""
    try:
        service = get_gmail_service(user_id=current_user.uid)
        body = req.model_dump(exclude_none=True)
        if not body:
            raise HTTPException(status_code=400, detail="No modification specified.")
        updated_message = service.users().messages().modify(userId='me', id=message_id, body=body).execute()
        return updated_message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-email")
async def send_email(req: SendEmailRequest, current_user: User = Depends(get_current_user)):
    """Sends an email from the authenticated user's account."""
    try:
        service = get_gmail_service(user_id=current_user.uid)
        message = MIMEText(req.body, 'html')
        message['to'] = req.to
        message['from'] = current_user.email
        message['subject'] = req.subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        return {"status": "success", "message_id": send_message['id']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/draft-reply")
async def draft_ai_reply(email: EmailContent, current_user: User = Depends(get_current_user)):
    """Instructs the AI agent to draft a reply for the authenticated user."""
    try:
        prompt = f"""Use the 'draft_reply_tool' to generate a response. The user's name is {current_user.name}.
        Email Subject: "{email.subject}"
        Email Snippet: "{email.snippet}"
        Perspective for reply: "{email.perspective}" """
        ai_response = await run_agent(prompt, user=current_user)
        return {"draft": ai_response.get("output")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message/{message_id}/agent-query")
async def query_agent_on_email(message_id: str, req: AgentQueryRequest, current_user: User = Depends(get_current_user)):
    """Takes a user's query about a specific email and returns the agent's response."""
    try:
        service = get_gmail_service(user_id=current_user.uid)
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        email_body_html = get_email_body(message.get('payload', {}))
        soup = BeautifulSoup(email_body_html, "html.parser")
        email_body_text = soup.get_text(separator='\n', strip=True)

        prompt = f"""A user named {current_user.name} is asking a question about an email. Use the email's content as context.
        USER'S QUESTION: "{req.query}"
        USER'S EMAIL ADDRESS (for context): "{current_user.email}"
        FULL EMAIL CONTENT:
        ---
        {email_body_text}
        ---
        """
        ai_response = await run_agent(prompt, user=current_user)
        return ai_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))