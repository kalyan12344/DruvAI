import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Any
from datetime import datetime, timezone
from firebase_admin import firestore

from api.routes.auth import User, get_current_user

router = APIRouter()

class ChatMessage(BaseModel):
    sender: str
    content: Any

@router.post("/history")
async def save_chat_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """Saves a single chat message to the user's history in Firestore."""
    try:
        db = firestore.client()
        doc_ref = db.collection('users').document(current_user.uid).collection('chat_history').document()
        
        message_data = {
            'sender': message.sender,
            'content': message.content,
            'timestamp': datetime.now(timezone.utc)
        }
        
        # FIX: Run the blocking .set() call in a separate thread
        await asyncio.to_thread(doc_ref.set, message_data)
        
        return {"status": "success", "message_id": doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_chat_history(current_user: User = Depends(get_current_user)):
    """Retrieves the chat history for the authenticated user."""
    try:
        db = firestore.client()
        
        # FIX: Run the blocking .stream() call in a separate thread
        docs_stream = await asyncio.to_thread(
            db.collection('users').document(current_user.uid).collection('chat_history').order_by('timestamp').stream
        )
        
        history = []
        for doc in docs_stream:
            data = doc.to_dict()
            if data['sender'] == 'user':
                history.append({'text': data['content'], 'sender': 'user'})
            else:
                history.append({'content': data['content'], 'sender': 'bot'})
        
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))