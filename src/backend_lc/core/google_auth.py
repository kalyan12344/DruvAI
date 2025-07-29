import json
import os
from firebase_admin import firestore, auth
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# --- Configuration ---
google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if not google_creds_json:
    raise ValueError("The GOOGLE_CREDENTIALS environment variable is not set.")
CLIENT_SECRETS_FILE = json.loads(google_creds_json)

REDIRECT_URI = 'http://127.0.0.1:8000/api/google/auth/callback'
SERVICE_SCOPES = {
    'calendar': ['https://www.googleapis.com/auth/calendar.events'],
    'gmail': ['https://www.googleapis.com/auth/gmail.modify'],
    'contacts': ['https://www.googleapis.com/auth/contacts.readonly']
}

# --- Credential Management ---
def _get_credentials_for_user(user_id: str, service: str) -> Credentials:
    """
    Fetches a user's stored Google credentials from Firestore, refreshing them if necessary.
    """
    db = firestore.client()
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise ValueError(f"User '{user_id}' not found in Firestore. Cannot get credentials.")

    user_data = user_doc.to_dict()
    creds_dict = user_data.get("google_credentials", {}).get(f"{service}_token")

    if not creds_dict:
        raise ValueError(f"User '{user_id}' has not authenticated with Google {service.capitalize()}.")

    creds = Credentials.from_authorized_user_info(creds_dict, SERVICE_SCOPES[service])

    # If credentials have expired and a refresh token exists, refresh them.
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleAuthRequest())
        # Persist the newly refreshed credentials back to Firestore.
        user_ref.set({
            "google_credentials": {f"{service}_token": json.loads(creds.to_json())}
        }, merge=True)
        print(f"Refreshed token for user {user_id} and service {service}")

    return creds

# --- Service Client Builders ---
def get_calendar_service(user_id: str):
    """Builds and returns a Google Calendar service client."""
    creds = _get_credentials_for_user(user_id, "calendar")
    return build('calendar', 'v3', credentials=creds)

def get_gmail_service(user_id: str):
    """Builds and returns a Gmail service client."""
    creds = _get_credentials_for_user(user_id, "gmail")
    return build('gmail', 'v1', credentials=creds)

def get_people_service(user_id: str):
    """Builds and returns a Google People API (Contacts) service client."""
    creds = _get_credentials_for_user(user_id, "contacts")
    return build('people', 'v1', credentials=creds)

# --- OAuth2 Flow Handlers ---
def get_google_auth_url(user_id: str, service: str) -> dict:
    """Generates a Google authentication URL for the user to visit."""
    flow = Flow.from_client_config(CLIENT_SECRETS_FILE, scopes=SERVICE_SCOPES[service], redirect_uri=REDIRECT_URI)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        state=f"{user_id}::{service}"  # Embed user_id and service in state
    )
    return {"authorization_url": authorization_url}

def process_google_callback(code: str, state: str) -> str:
    """
    Handles the OAuth2 callback from Google, exchanges the code for credentials,
    and saves them to Firestore. Creates the user document if it's the first write.
    """
    try:
        user_id, service = state.split("::")
    except ValueError:
        raise ValueError("Invalid state parameter received from Google.")
        
    flow = Flow.from_client_config(CLIENT_SECRETS_FILE, scopes=SERVICE_SCOPES[service], redirect_uri=REDIRECT_URI)
    flow.fetch_token(code=code)
    credentials = flow.credentials

    db = firestore.client()
    user_ref = db.collection('users').document(user_id)
    
    # This command creates the document if it doesn't exist, or updates it if it does.
    user_ref.set({
        "google_credentials": {f"{service}_token": json.loads(credentials.to_json())}
    }, merge=True)
    
    # Optionally, you can also store the user's email at this point.
    try:
        user_info = auth.get_user(user_id)
        if user_info.email:
            user_ref.set({"email": user_info.email}, merge=True)
            return user_info.email
    except Exception as e:
        print(f"Could not fetch user info for {user_id}: {e}")

    return "Unknown Email"