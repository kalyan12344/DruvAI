from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from firebase_admin import storage, firestore
import os

from .vector_store import get_user_collection

def index_document_in_background(
    user_id: str,
    document_id: str, # FIX: Accept the document_id
    file_path: str,
    original_filename: str
):
    """
    This function runs in the background to process an uploaded file.
    """
    print(f"BACKGROUND TASK: Starting to index '{original_filename}' (doc_id: {document_id}) for user {user_id}")
    db = firestore.client()
    # Get a reference to the document we already created in the API endpoint
    doc_ref = db.collection('users').document(user_id).collection('documents').document(document_id)
    
    try:
        bucket = storage.bucket()
        blob = bucket.blob(file_path)
        temp_file_path = f"/tmp/{original_filename}"
        blob.download_to_filename(temp_file_path)

        loader = PyPDFLoader(temp_file_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(documents)
        print(f"-> Split document into {len(chunks)} chunks.")
        
        collection = get_user_collection(user_id)

        collection.add(
            documents=[chunk.page_content for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
            ids=[f"{document_id}_{i}" for i in range(len(chunks))]
        )
        print(f"-> Successfully indexed chunks in ChromaDB for user {user_id}")
        
        # FIX: Update the existing document's status to 'Indexed'
        doc_ref.update({
            "status": "Indexed",
            "indexed_at": firestore.SERVER_TIMESTAMP,
            "chunk_count": len(chunks)
        })
        
        print(f"BACKGROUND TASK: Finished indexing for user {user_id}")
        os.remove(temp_file_path)

    except Exception as e:
        print(f"🔥 BACKGROUND TASK FAILED for user {user_id}: {e}")
        # FIX: Update the document status to 'Error' if something goes wrong
        doc_ref.update({"status": "Error", "error_message": str(e)})