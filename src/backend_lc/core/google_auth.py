# In your google_auth.py or equivalent file

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- SCOPES (UPDATED) ---
# Changed gmail.readonly to gmail.modify to allow sending and replying.
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify'
]

# --- Internal Helper for Authentication ---
def _get_google_credentials():
    """
    Internal function to handle Google API authentication flow.
    Returns valid credentials for the defined SCOPES.
    """
    creds = None
    if os.path.exists('ctoken.json'):
        creds = Credentials.from_authorized_user_file('ctoken.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("No valid credentials found. Starting authentication flow for new permissions...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('ctoken.json', 'w') as token:
            print("Saving new credentials to ctoken.json...")
            token.write(creds.to_json())
            
    return creds

# --- Service Getters ---

def get_calendar_service():
    """Returns an authorized Google Calendar API service instance."""
    print("Initializing Google Calendar service...")
    creds = _get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)
    print("Google Calendar service initialized successfully.")
    return service

def get_gmail_service():
    """Returns an authorized Gmail API service instance."""
    print("Initializing Gmail service...")
    creds = _get_google_credentials()
    service = build('gmail', 'v1', credentials=creds)
    print("Gmail service initialized successfully.")
    return service