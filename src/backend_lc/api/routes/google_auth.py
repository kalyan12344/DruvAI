# api/routes/google_auth.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
import json
import requests
# Import configuration from the core module
from core.google_auth import CLIENT_SECRETS_FILE, TOKEN_FILE, BASE_SCOPES, SERVICE_SCOPES

router = APIRouter()
REDIRECT_URI = 'http://127.0.0.1:8000/api/google/auth/callback'

# Helper functions to read/write your db.json
def read_app_db():
    with open("db.json", 'r') as f:
        return json.load(f)

def write_app_db(data):
    with open("db.json", 'w') as f:
        json.dump(data, f, indent=2)


@router.get("/login")
async def google_auth_login(service: str):
    """
    Initiates the Google OAuth 2.0 flow for a specific service (e.g., 'calendar' or 'gmail').
    """
    if service not in SERVICE_SCOPES:
        raise HTTPException(status_code=400, detail="Invalid service requested")

    # Dynamically build the list of scopes for the requested service
    required_scopes = BASE_SCOPES + SERVICE_SCOPES[service]

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=required_scopes,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent', # Ensures a refresh token is always issued
        include_granted_scopes='true'
    )
    return RedirectResponse(authorization_url)


@router.get("/callback")
async def google_auth_callback(request: Request, code: str, scope: str):
    """
    Handles the callback from Google, exchanges the code for tokens, and updates app state.
    """
    # Use the scopes actually granted by the user (returned by Google) to prevent mismatch errors.
    granted_scopes = scope.split()

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=granted_scopes,
        redirect_uri=REDIRECT_URI
    )
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Save the credentials with their specific scopes to token.json
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())

        # Get user email
        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        user_email = userinfo_response.json().get('email', '')

        # Update db.json to mark the service as connected
        db_data = read_app_db()
        if 'https://www.googleapis.com/auth/calendar' in granted_scopes:
            db_data["connected_calendars"]["google"]["connected"] = True
            db_data["connected_calendars"]["google"]["user_email"] = user_email
            print(f"✅ Successfully connected Google Calendar for user: {user_email}")
        # Add a similar check here for gmail if you implement it
        
        write_app_db(db_data)
        
        return HTMLResponse('<script>window.close();</script>')

    except Exception as e:
        print(f"❌ An error occurred in the callback flow: {e}")
        return HTMLResponse('<script>alert("An error occurred during authentication."); window.close();</script>')