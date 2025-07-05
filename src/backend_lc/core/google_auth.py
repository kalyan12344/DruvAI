import os
import json
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError, OAuthError
from google_auth_oauthlib.flow import Flow

# --- CONFIGURATION ---
CLIENT_SECRETS_FILE = 'credentials.json'
REDIRECT_URI = 'http://127.0.0.1:8000/api/google/auth/callback'
CALENDAR_TOKEN_FILE = "token_calendar.json"
GMAIL_TOKEN_FILE = "token_gmail.json"
PEOPLE_TOKEN_FILE = "token_people.json" # Token file for contacts

BASE_SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 'openid']

# Service-specific scopes required for each API
SERVICE_SCOPES = {
    'calendar': ['https://www.googleapis.com/auth/calendar'],
    'gmail': ['https://www.googleapis.com/auth/gmail.modify'],
    'contacts': ['https://www.googleapis.com/auth/contacts.readonly']
}

# --- DB & AUTH LOGIC ---

def read_app_db():
    """Reads the connection status from db.json."""
    try:
        if os.path.exists("db.json") and os.path.getsize("db.json") > 0:
            with open("db.json", 'r') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Could not read db.json: {e}. Returning default structure.")
    
    # Return a default structure if the file is missing or empty
    return {
      "connected_calendars": {},
      "connected_mails": {},
      "connected_contacts": {} # Add a section for contacts status
    }

def write_app_db(data):
    """Writes data to the db.json file."""
    with open("db.json", 'w') as f:
        json.dump(data, f, indent=2)

class SecurityException(Exception):
    pass

def get_google_auth_url(service: str):
    """Generates the Google authorization URL for a specific service."""
    if service not in SERVICE_SCOPES:
        raise ValueError(f"Invalid service requested: {service}")

    required_scopes = BASE_SCOPES + SERVICE_SCOPES[service]
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=required_scopes,
        redirect_uri=REDIRECT_URI
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    
    return {
        "authorization_url": authorization_url,
        "state": state,
        "scopes": required_scopes
    }

def process_google_callback(code: str, state: str, session_state: str, original_scopes: list):
    """Processes the callback from Google, saving tokens for all granted scopes."""
    if not session_state or session_state != state:
        raise SecurityException("State mismatch. Possible CSRF attack.")
    if not original_scopes:
        raise ValueError("Original scope information is missing.")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=original_scopes,
        redirect_uri=REDIRECT_URI
    )
    
    flow.fetch_token(code=code) 
    credentials = flow.credentials

    user_info_res = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {credentials.token}'}
    )
    user_info_res.raise_for_status()
    user_email = user_info_res.json().get('email', 'N/A')

    db_data = read_app_db()
    
    # Defensively ensure keys exist
    if "connected_calendars" not in db_data: db_data["connected_calendars"] = {}
    if "connected_mails" not in db_data: db_data["connected_mails"] = {}
    if "connected_contacts" not in db_data: db_data["connected_contacts"] = {}
        
    granted_scopes = credentials.scopes

    # Check for each service scope and save the token if present
    if any('auth/calendar' in s for s in granted_scopes):
        with open(CALENDAR_TOKEN_FILE, 'w') as token_file:
            token_file.write(credentials.to_json())
        db_data["connected_calendars"]["google"] = {"connected": True, "user_email": user_email}
    
    if any('auth/gmail' in s for s in granted_scopes):
        with open(GMAIL_TOKEN_FILE, 'w') as token_file:
            token_file.write(credentials.to_json())
        db_data["connected_mails"]["google_gmail"] = {"connected": True, "user_email": user_email}

    if any('auth/contacts' in s for s in granted_scopes):
        with open(PEOPLE_TOKEN_FILE, 'w') as token_file:
            token_file.write(credentials.to_json())
        db_data["connected_contacts"]["google"] = {"connected": True, "user_email": user_email}

    write_app_db(db_data)
    return user_email

# --- SERVICE GETTERS ---

def _get_credentials(token_file: str):
    """Loads and refreshes credentials from a specific token file."""
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(GoogleAuthRequest())
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            except RefreshError as e:
                print(f"❌ Error refreshing token for {token_file}: {e}. User needs to re-authenticate.")
                os.remove(token_file)
                return None
        else:
            return None
    return creds

def get_calendar_service():
    """Returns an authorized Google Calendar API service instance."""
    creds = _get_credentials(CALENDAR_TOKEN_FILE)
    if not creds:
        raise Exception("Google Calendar not connected. Please authenticate.")
    return build('calendar', 'v3', credentials=creds)

def get_gmail_service():
    """Returns an authorized Gmail API service instance."""
    creds = _get_credentials(GMAIL_TOKEN_FILE)
    if not creds:
        raise Exception("Gmail not connected. Please authenticate.")
    return build('gmail', 'v1', credentials=creds)

def get_people_service():
    """Returns an authorized Google People API service instance."""
    creds = _get_credentials(PEOPLE_TOKEN_FILE)
    if not creds:
        raise Exception("Google Contacts not connected. Please authenticate.")
    return build('people', 'v1', credentials=creds)
