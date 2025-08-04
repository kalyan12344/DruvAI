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


@router.delete("/history")
async def clear_chat_history(current_user: User = Depends(get_current_user)):
    """Deletes all messages in the user's chat history."""
    try:
        db = firestore.client()
        collection_ref = db.collection('users').document(current_user.uid).collection('chat_history')
        
        # Firestore doesn't have a direct collection delete, so we delete in a batch
        def delete_collection():
            batch = db.batch()
            docs = collection_ref.limit(500).stream() # Delete up to 500 docs at a time
            deleted = 0
            for doc in docs:
                batch.delete(doc.reference)
                deleted += 1
            
            if deleted > 0:
                batch.commit()
            return deleted

        # Run the synchronous delete operation in a separate thread
        deleted_count = await asyncio.to_thread(delete_collection)
        
        print(f"Cleared {deleted_count} messages for user {current_user.uid}")
        return {"status": "success", "message": f"Chat history with {deleted_count} messages cleared."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))