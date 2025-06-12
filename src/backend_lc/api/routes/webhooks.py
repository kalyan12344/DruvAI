# api/routes/webhooks.py

import base64
import json
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from datetime import datetime
import openpyxl
import os
import traceback

# Adjust these imports to match your project structure
from core.google_auth import get_gmail_service
from lc.config import get_llm_for_categorization

router = APIRouter()
EXCEL_FILENAME = "job_application_tracker.xlsx"
PROCESSED_IDS_LOG = "processed_ids.txt" # Simple text file to log processed email IDs

# --- Helper Functions ---

def _get_email_body(payload: dict) -> str:
    # ... (this function remains the same)
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
    elif 'body' in payload:
        data = payload['body'].get('data')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')
    return ""

def _log_job_email_to_excel(date: str, details: dict, sender: str, subject: str):
    # ... (this function remains the same)
    print(f"✅ Logging extracted job details to {EXCEL_FILENAME}...")
    headers = ["Date Received", "Company Name", "Status", "Mentioned Date", "From", "Subject"]
    new_row = [date, details.get("companyName", "N/A"), details.get("status", "N/A"), details.get("date", "N/A"), sender, subject]
    if not os.path.exists(EXCEL_FILENAME):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.append(headers)
    else:
        workbook = openpyxl.load_workbook(EXCEL_FILENAME)
        sheet = workbook.active
    sheet.append(new_row)
    workbook.save(EXCEL_FILENAME)
    print("✅ Successfully logged structured data to Excel.")

def _extract_job_details_with_llm(subject: str, body: str) -> dict | None:
    # ... (this function remains the same)
    print("🧠 Using LLM to extract job application details...")
    status_options = ["Applied","Interview Scheduled", "Online Assessment", "Offer Extended", "Application Received", "Update / In Progress", "Rejected", "Not a job email"]
    prompt = (
        f"Your task is to analyze an email...  "
        f" You should only consider the job application related emails" # Keeping this brief for clarity
        f"Respond with ONLY a JSON object in the format: {{\"companyName\": \"...\", \"status\": \"...\", \"date\": \"YYYY-MM-DD\"}}\n\n"
        f"For the 'status' field, you MUST use one of these exact options: {', '.join(status_options)}\n"
        f"If you cannot find a piece of information, use 'N/A' for that value.\n\n"
        f"--- Email --- \nSubject: {subject}\n\nBody: {body[:2500]}\n--- End Email ---\n\nJSON Response:"
    )
    try:
        llm = get_llm_for_categorization()
        response = llm.invoke(prompt)
        result_text = response.content.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        details = json.loads(result_text)
        if details.get("status") == "Not a job email":
            return None
        return details
    except Exception as e:
        print(f"❌ LLM extraction failed: {e}")
        return None

# --- NEW: Helper functions to track processed emails ---
def _is_message_processed(message_id: str) -> bool:
    """Checks if a message ID has already been logged."""
    if not os.path.exists(PROCESSED_IDS_LOG):
        return False
    with open(PROCESSED_IDS_LOG, 'r') as f:
        processed_ids = {line.strip() for line in f}
    return message_id in processed_ids

def _mark_message_as_processed(message_id: str):
    """Adds a message ID to the log file."""
    with open(PROCESSED_IDS_LOG, 'a') as f:
        f.write(f"{message_id}\n")

# --- Main Processing Function (Now with duplicate checking) ---
def process_new_email(message: dict):
    """
    This function now checks for duplicate notifications before processing.
    """
    try:
        newest_message_id = message.get('messageId')
        if not newest_message_id:
            return

        print(f"📬 Notification received for new message. Message ID: {newest_message_id}")

        # --- NEW: Check if this message has already been processed ---
        if _is_message_processed(newest_message_id):
            print(f"Duplicate notification for message {newest_message_id}. Skipping.")
            return
        
        service = get_gmail_service()
        response = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=1).execute()
        messages = response.get('messages', [])
        if not messages:
            return
            
        real_message_id = messages[0]['id']
        print(f"Found newest message with real ID: {real_message_id}")
        
        # We will also check the real ID to be extra safe
        if _is_message_processed(real_message_id):
            print(f"Duplicate real message ID {real_message_id}. Skipping.")
            return

        msg = service.users().messages().get(userId='me', id=real_message_id, format='full').execute()

        # ... (rest of the processing logic is the same)
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        date_received = next((h['value'] for h in headers if h['name'].lower() == 'date'), str(datetime.now()))
        
        print(f"   From: {sender}")
        print(f"   Subject: {subject}")
        
        full_body = _get_email_body(payload)
        extracted_details = _extract_job_details_with_llm(subject, full_body)
        
        if extracted_details:
            print(f"🧠 LLM extracted job details: {extracted_details}")
            _log_job_email_to_excel(date_received, extracted_details, sender, subject)
        else:
            print("🧠 LLM determined email was not job-related. No action taken.")
        
        # --- NEW: Mark this message as processed so it won't run again ---
        _mark_message_as_processed(real_message_id)
        # Also log the pub/sub id to be safe
        _mark_message_as_processed(newest_message_id)

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"❌❌❌ AN ERROR OCCURRED ❌❌❌\n{error_details}")
        with open("webhook_error_log.txt", "a") as f:
            f.write(f"--- {datetime.now()} ---\n{error_details}\n\n")

# --- FastAPI Router (No changes needed here) ---
@router.post("/gmail-push")
async def gmail_webhook_receiver(request: Request, background_tasks: BackgroundTasks):
    # ... (this function remains the same)
    print("Received a request on /gmail-push...")
    try:
        payload = await request.json()
        if payload and 'message' in payload:
            background_tasks.add_task(process_new_email, payload['message'])
            return {"status": "success"}, 200
        else:
            print("Received a verification request.")
            return {"status": "ok"}, 200
    except Exception as e:
        print(f"Error in webhook endpoint: {e}")
        raise HTTPException(status_code=400, detail="Invalid request payload")