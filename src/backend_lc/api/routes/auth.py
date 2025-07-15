#api/routes/auth.py
import firebase_admin
from firebase_admin import auth
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# This file is the cornerstone of your security.

router = APIRouter()

# --- Pydantic Model for User Data ---
class User(BaseModel):
    email: str
    uid: str

# --- OAuth2 Scheme & The "Gatekeeper" Dependency ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # URL is a placeholder

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    This dependency runs on every protected endpoint.
    It verifies the Firebase ID token from the Authorization header
    and returns the user's data. If the token is invalid, it stops the request.
    """
    try:
        print("token from frontend to get current user", token)
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        user_record = auth.get_user(uid)
        print(user_record)
        return User(email=user_record.email, uid=user_record.uid)
    except Exception as e:
        # --- ADD THESE TWO LINES TO SEE THE REAL ERROR ---
        print(f"🔥 VERIFICATION FAILED. ERROR TYPE: {type(e).__name__}")
        print(f"🔥 ERROR DETAILS: {e}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
