#api/routes/google_auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from core.google_auth import get_google_auth_url, process_google_callback
from api.routes.auth import User, get_current_user 

router = APIRouter()

@router.get("/login-url")
def get_auth_url(service: str, current_user: User = Depends(get_current_user)):
    """Provides a Google auth URL for the currently authenticated user."""
    try:
        auth_data = get_google_auth_url(user_id=current_user.uid, service=service)
        return auth_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
def oauth_callback(code: str, state: str):
    """Handles the OAuth2 callback from Google."""
    try:
        user_email = process_google_callback(code=code, state=state)
        return HTMLResponse(f'<html><body><h1>Success!</h1><p>Authenticated as {user_email}. You can close this window.</p><script>window.close();</script></body></html>')
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))