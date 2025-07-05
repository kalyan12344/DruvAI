# api/routes/google_auth.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import requests

# Import the specific logic functions and custom exceptions from the core module
from core.google_auth import (
    get_google_auth_url,
    process_google_callback,
    SecurityException
)
# Import the correct exception class from the google.auth library
from google.auth.exceptions import OAuthError

router = APIRouter()

@router.get("/login", response_model=None)
async def google_auth_login_route(request: Request, service: str):
    """Initiates the Google OAuth 2.0 flow for a specific service."""
    try:
        auth_data = get_google_auth_url(service)
        
        # Store state and scopes in the session
        request.session['state'] = auth_data["state"]
        request.session['auth_scopes'] = auth_data["scopes"]
        
        return RedirectResponse(auth_data["authorization_url"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/callback")
async def google_auth_callback_route(request: Request, code: str, state: str):
    """Handles the callback from Google."""
    try:
        user_email = process_google_callback(
            code=code,
            state=state,
            session_state=request.session.get('state'),
            original_scopes=request.session.get('auth_scopes')
        )
        
        print(f"✅ Successfully authenticated and saved credentials for {user_email}.")

        # Clean up the session
        request.session.pop('state', None)
        request.session.pop('auth_scopes', None)
        
        return HTMLResponse('<script>window.close();</script>')

    except (SecurityException, ValueError, OAuthError, requests.exceptions.HTTPError) as e:
        # Catch the specific errors we expect from our logic
        error_message = f"An authentication error occurred: {e}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch any other unexpected errors
        print(f"❌ An unexpected server error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected server error occurred.")