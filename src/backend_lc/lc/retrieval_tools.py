import chromadb
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from typing import Optional

from .vector_store import get_user_collection

class DocumentSearchArgs(BaseModel):
    query: str = Field(..., description="The user's question or topic to search for in their documents.")
    filename: Optional[str] = Field(None, description="The specific filename to search within. If omitted, all documents will be searched.")

@tool(args_schema=DocumentSearchArgs)
def search_user_documents(*, query: str, user_id: str, filename: Optional[str] = None) -> str:
    """
    Searches a user's private, indexed documents to find context relevant to their query.
    If a filename is provided, the search is intelligently limited to only that document.
    """
    print(f"Retrieving documents for user '{user_id}' with query '{query}'")
    if filename:
        print(f"--> Filtering search to document: {filename}")
        
    try:
        collection = get_user_collection(user_id)
        
        # Add a 'where' filter if a specific filename is provided
        if filename:
            results = collection.query(
                query_texts=[query],
                n_results=5,
                where={"source": filename} # Assumes the loader's metadata includes a 'source' key
            )
        else:
            # If no filename, search all documents in the user's collection
            results = collection.query(
                query_texts=[query],
                n_results=5
            )

        if not results or not results.get('documents') or not results['documents'][0]:
            return "No relevant information was found in the user's documents."

        # Combine the found documents into a single context string
        context = "\n---\n".join(results['documents'][0])
        return f"Found the following context from the user's documents:\n{context}"

    except Exception as e:
        print(f"Error retrieving from ChromaDB for user {user_id}: {e}")
        # Check if the error is due to a non-existent collection
        if "does not exist" in str(e):
             return "The user has not uploaded any documents yet."
        return "An error occurred while searching the documents."