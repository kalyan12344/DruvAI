from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from core.google_auth import get_gmail_service
from lc.react_agent import run_agent # Imports your custom agent

import base64
from bs4 import BeautifulSoup
import json
from email.mime.text import MIMEText
from datetime import datetime


router = APIRouter()

# --- Pydantic Models for Request Bodies ---
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


# --- Helper Functions ---

def get_email_body(payload):
    """Recursively search for the email body (preferring HTML) and decode it."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/html':
                data = part['body'].get('data', '')
                return base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
            # Recurse into nested parts to find the body
            body = get_email_body(part)
            if body:
                return body
    elif 'body' in payload and payload['body'].get('data'):
        data = payload['body']['data']
        return base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
    return "" # Return empty string if no body is found

def _fetch_and_format_messages(service, message_ids):
    """Helper to fetch metadata for a list of message IDs and format them."""
    if not message_ids:
        return []
    
    formatted_messages = []
    for msg_summary in message_ids:
        msg_id = msg_summary['id']
        message = service.users().messages().get(userId='me', id=msg_id, format='metadata').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'No Sender')
        
        formatted_messages.append({
            'id': message['id'],
            'threadId': message['threadId'],
            'snippet': message.get('snippet', ''),
            'subject': subject,
            'from': sender.split('<')[0].strip(),
        })
    return formatted_messages


# --- API Endpoints ---

@router.get("/status")
async def get_mail_connection_status():
    """Gets the connection status for Google Gmail."""
    try:
        with open("db.json", 'r') as f:
            db_data = json.load(f)
        return db_data.get("connected_mails", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

@router.get("/messages")
async def get_gmail_messages():
    """Gets the latest messages from the INBOX."""
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=25).execute()
        message_ids = results.get('messages', [])
        return _fetch_and_format_messages(service, message_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/search")
async def search_emails(q: str):
    """Searches the user's entire mailbox for a query."""
    if not q:
        raise HTTPException(status_code=400, detail="A search query 'q' is required.")
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', q=q, maxResults=25).execute()
        message_ids = results.get('messages', [])
        return _fetch_and_format_messages(service, message_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during search: {str(e)}")

@router.get("/message/{message_id}")
async def get_single_email(message_id: str):
    """Fetches the full content of a single email."""
    try:
        service = get_gmail_service()
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'No Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        body_html = get_email_body(payload)
        if body_html:
            soup = BeautifulSoup(body_html, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            body_html = str(soup)

        return {'id': message['id'], 'subject': subject, 'from': sender, 'date': date, 'snippet': message.get('snippet', ''), 'body': body_html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/message/{message_id}/modify")
async def modify_email(message_id: str, req: ModifyRequest):
    """Modifies an email's labels (e.g., to archive or mark as read)."""
    try:
        service = get_gmail_service()
        body = req.dict(exclude_none=True)
        if not body:
            raise HTTPException(status_code=400, detail="No modification specified.")
        updated_message = service.users().messages().modify(userId='me', id=message_id, body=body).execute()
        return updated_message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to modify email: {str(e)}")

@router.post("/send-email")
async def send_email(req: SendEmailRequest):
    """Creates and sends an email using the Gmail API."""
    try:
        service = get_gmail_service()
        message = MIMEText(req.body, 'html')
        message['to'] = req.to
        message['subject'] = req.subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        return {"message_id": send_message['id'], "status": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@router.post("/draft-reply")
async def draft_ai_reply(email: EmailContent):
    """
    Instructs the AI agent to use the 'draft_reply_tool' with the given perspective.
    """
    try:
        prompt = f"""
        Please use the 'draft_reply_tool' to generate a response for the following email.
        
        - Subject: "{email.subject}"
        - Snippet: "{email.snippet}"
        - Perspective for the reply: "{email.perspective}"
        """

        print(f"--- Instructing agent to use draft_reply_tool ---")
        ai_response = run_agent(prompt)
        print(f"--- Agent finished. Final response received. ---")

        return {"draft": ai_response}

    except Exception as e:
        print(f"An error occurred calling the AI agent: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while communicating with the AI agent: {str(e)}")


# --- NEW ENDPOINT FOR "ASK AI" FEATURE ---
@router.post("/message/{message_id}/agent-query")
def query_agent_on_email(message_id: str, req: AgentQueryRequest):
    """
    Takes a user's query about a specific email, provides the email content as context,
    and returns the agent's response. This is a SYNCHRONOUS endpoint to be compatible
    with Playwright's sync API.
    """
    try:
        # Step 1: Get the full content of the email the user is looking at.
        service = get_gmail_service()
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        email_body_html = get_email_body(message.get('payload', {}))
        
        soup = BeautifulSoup(email_body_html, "html.parser")
        email_body_text = soup.get_text(separator='\n', strip=True)

        # Step 2: Create a detailed prompt that bundles the user's question with the email context.
        prompt = f"""
        You are Druv, an AI assistant. Your user is currently looking at a specific email and has asked a question about it.
        Your mission is to use the provided email content as context to answer the user's question accurately.
        Use your tools if necessary. For example, if the user asks to track a package, use the 'nike_order_lookup' tool.

        **USER'S QUESTION:**
        "{req.query}"
        
        **USER'S EMAIL ADDRESS (for order lookups):**
        "kalyanraju90@gmail.com"

        **FULL EMAIL CONTENT FOR CONTEXT:**
        ---
        {email_body_text}
        ---

        Now, begin your thought process to answer the user's question.
        """

        print(f"--- Calling agent with contextual query: {req.query} ---")
        ai_response = run_agent(prompt)
        print(f"--- Agent finished. Final response received. ---")

        return {"response": ai_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")