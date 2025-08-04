import asyncio
from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
from api.routes.auth import User, get_current_user

router = APIRouter()

@router.get("/list")
async def list_user_documents(current_user: User = Depends(get_current_user)):
    """Retrieves a list of all indexed documents for the authenticated user."""
    try:
        db = firestore.client()
        docs_ref = db.collection('users').document(current_user.uid).collection('documents')
        
        docs_stream = await asyncio.to_thread(docs_ref.stream)
        
        documents = []
        for doc in docs_stream:
            doc_data = doc.to_dict()
            if doc_data.get("status") == "Indexed":
                documents.append({
                    "id": doc.id,
                    "filename": doc_data.get("filename")
                })
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{document_id}")
async def get_document_status(document_id: str, current_user: User = Depends(get_current_user)):
    """Checks the processing status of a specific document for the user."""
    try:
        db = firestore.client()
        doc_ref = db.collection('users').document(current_user.uid).collection('documents').document(document_id)
        
        # Run the synchronous .get() call in a separate thread to avoid blocking
        doc = await asyncio.to_thread(doc_ref.get)

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found or access denied.")
        
        return doc.to_dict()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))