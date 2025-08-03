import json
import os
import asyncio
from firebase_admin import firestore, auth
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
CLIENT_SECRETS_FILE = json.loads(google_creds_json)

# FIX: Use an environment variable for the redirect URI
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:8000")
REDIRECT_URI = f"{BACKEND_BASE_URL}/api/google/auth/callback"

SERVICE_SCOPES = {
    'calendar': ['https://www.googleapis.com/auth/calendar.events'],
    'gmail': ['https://www.googleapis.com/auth/gmail.modify'],
    'contacts': ['https://www.googleapis.com/auth/contacts.readonly']
}

async def _get_credentials_for_user(user_id: str, service: str):
    db = firestore.client()
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise ValueError("User not found in Firestore.")
    user_data = user_doc.to_dict()
    creds_dict = user_data.get("google_credentials", {}).get(f"{service}_token")
    if not creds_dict:
        raise ValueError(f"User has not authenticated with Google {service.capitalize()}.")
    creds = Credentials.from_authorized_user_info(creds_dict, SERVICE_SCOPES[service])
    if creds and creds.expired and creds.refresh_token:
        await asyncio.to_thread(creds.refresh, GoogleAuthRequest())
        user_ref.set({"google_credentials": {f"{service}_token": json.loads(creds.to_json())}}, merge=True)
    return creds

async def get_calendar_service(user_id: str):
    creds = await _get_credentials_for_user(user_id, "calendar")
    return build('calendar', 'v3', credentials=creds)

async def get_gmail_service(user_id: str):
    creds = await _get_credentials_for_user(user_id, "gmail")
    return build('gmail', 'v1', credentials=creds)

async def get_people_service(user_id: str):
    creds = await _get_credentials_for_user(user_id, "contacts")
    return build('people', 'v1', credentials=creds)

def get_google_auth_url(user_id: str, service: str) -> dict:
    flow = Flow.from_client_config(CLIENT_SECRETS_FILE, scopes=SERVICE_SCOPES[service], redirect_uri=REDIRECT_URI)
    authorization_url, state = flow.authorization_url(
        access_type='offline', prompt='consent', state=f"{user_id}::{service}"
    )
    return {"authorization_url": authorization_url}

def process_google_callback(code: str, state: str):
    try:
        user_id, service = state.split("::")
    except ValueError:
        raise ValueError("Invalid state parameter.")
    flow = Flow.from_client_config(CLIENT_SECRETS_FILE, scopes=SERVICE_SCOPES[service], redirect_uri=REDIRECT_URI)
    flow.fetch_token(code=code)
    credentials = flow.credentials
    db = firestore.client()
    user_ref = db.collection('users').document(user_id)
    user_info = auth.get_user(user_id)
    
    update_data = {f"google_credentials.{service}_token": json.loads(credentials.to_json())}
    
    # FIX: Correctly update the status field based on the service
    if service == 'calendar':
        update_data[f"calendars.google"] = {"connected": True, "email": user_info.email}
    elif service == 'gmail':
        update_data[f"mails.google"] = {"connected": True, "email": user_info.email}
    
    user_ref.update(update_data)
    return user_info.email