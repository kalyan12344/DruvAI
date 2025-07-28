import json
import os
from firebase_admin import firestore, auth
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# --- Load Secrets from Environment Variables (More Secure for Deployment) ---
# In your Cloud Run service, you will set these variables.
GOOGLE_SECRETS_JSON = os.environ.get("GOOGLE_CREDENTIALS")
if not GOOGLE_SECRETS_JSON:
    raise ValueError("CRITICAL: GOOGLE_CREDENTIALS environment variable is not set.")

# This is now a dictionary, not a file path
CLIENT_SECRETS_DICT = json.loads(GOOGLE_SECRETS_JSON)

# The Redirect URI should also be an environment variable
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", 'http://127.0.0.1:8000/api/google/auth/callback')


SERVICE_SCOPES = {
    'calendar': ['https://www.googleapis.com/auth/calendar.events'],
    'gmail': ['https://www.googleapis.com/auth/gmail.modify'],
    'contacts': ['https://www.googleapis.com/auth/contacts.readonly']
}

db = firestore.client()

def _get_credentials_for_user(user_id: str, service: str):
    """Fetches a user's stored Google credentials from Firestore and refreshes if needed."""
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise ValueError("User not found in Firestore.")

    user_data = user_doc.to_dict()
    creds_dict = user_data.get("google_credentials", {}).get(f"{service}_token")

    if not creds_dict:
        raise ValueError(f"User has not authenticated with Google {service.capitalize()}.")

    creds = Credentials.from_authorized_user_info(creds_dict)

    if creds and creds.expired and creds.refresh_token:
        print(f"Refreshing token for user {user_id}, service: {service}")
        creds.refresh(GoogleAuthRequest())
        user_ref.set({
            "google_credentials": {f"{service}_token": json.loads(creds.to_json())}
        }, merge=True)
        print(f"Refreshed and saved new token for user {user_id}.")

    return creds

def get_service_for_user(user_id: str, service_name: str, version: str):
    """Builds a Google API service object for a specific user."""
    creds = _get_credentials_for_user(user_id, service_name.lower())
    return build(service_name, version, credentials=creds)


def get_google_auth_url(user_id: str, service: str):
    """Generates an auth URL with the user's ID embedded in the state."""
    # --- THIS IS THE FIX ---
    # Use from_client_config() to load from a dictionary instead of a file.
    flow = Flow.from_client_config(
        CLIENT_SECRETS_DICT,
        scopes=SERVICE_SCOPES[service],
        redirect_uri=REDIRECT_URI
    )
    # --- END OF FIX ---

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        state=f"{user_id}::{service}" # Embed user_id and service
    )
    return {"authorization_url": authorization_url}

def process_google_callback(code: str, state: str):
    """Processes the callback, extracting user_id and service from the state."""
    try:
        user_id, service = state.split("::")
    except ValueError:
        raise ValueError("Invalid state parameter.")

    # --- THIS IS THE FIX ---
    # Also use from_client_config() here for consistency.
    flow = Flow.from_client_config(
        CLIENT_SECRETS_DICT,
        scopes=SERVICE_SCOPES[service],
        redirect_uri=REDIRECT_URI
    )
    # --- END OF FIX ---

    flow.fetch_token(code=code)
    credentials = flow.credentials

    user_ref = db.collection('users').document(user_id)
    user_info = auth.get_user(user_id)
    
    user_ref.set({
        "google_credentials": {f"{service}_token": json.loads(credentials.to_json())},
        "email": user_info.email
    }, merge=True)
    
    return user_info.email
