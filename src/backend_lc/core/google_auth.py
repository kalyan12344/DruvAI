# core/google_auth.py

import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

# --- SINGLE SOURCE OF TRUTH FOR CONFIGURATION ---
CLIENT_SECRETS_FILE = 'credentials.json'
TOKEN_FILE = "token.json"

# Base scopes always requested
BASE_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email'
]

# Service-specific scopes
SERVICE_SCOPES = {
    'calendar': ['https://www.googleapis.com/auth/calendar'],
    'gmail': ['https://www.googleapis.com/auth/gmail.modify']
}

# --- Internal Helper for Authentication ---
def _get_google_credentials():
    """
    Loads credentials from token.json. Refreshes them if they have expired.
    Returns None if no valid credentials can be found or created.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                # Save the newly refreshed credentials for next time
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except RefreshError as e:
                print(f"❌ Error refreshing token: {e}. User needs to re-authenticate.")
                os.remove(TOKEN_FILE) # Delete the bad token
                return None
        else:
            return None # No token exists, user must authenticate via the web flow.
            
    return creds

# --- Service Getters ---
def get_calendar_service():
    """Returns an authorized Google Calendar API service instance."""
    print("Initializing Google Calendar service...")
    creds = _get_google_credentials()
    if not creds:
        raise Exception("User not authenticated. Please log in to connect Google Calendar.")
    
    # Verify that the necessary scope was granted
    if 'https://www.googleapis.com/auth/calendar' not in creds.scopes:
        raise Exception("Calendar permission not granted. Please re-authenticate and grant calendar access.")

    service = build('calendar', 'v3', credentials=creds)
    print("✅ Google Calendar service initialized successfully.")
    return service

def get_gmail_service():
    """Returns an authorized Gmail API service instance."""
    print("Initializing Gmail service...")
    creds = _get_google_credentials()
    if not creds:
        raise Exception("User not authenticated. Please log in to connect Gmail.")

    # Verify that the necessary scope was granted
    if 'https://www.googleapis.com/auth/gmail.modify' not in creds.scopes:
        raise Exception("Gmail permission not granted. Please re-authenticate and grant Gmail access.")

    service = build('gmail', 'v1', credentials=creds)
    print("✅ Gmail service initialized successfully.")
    return service