import chromadb
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from typing import Optional

from .vector_store import get_user_collection

class DocumentSearchArgs(BaseModel):
    query: str = Field(..., description="The user's question or topic to search for in their documents.")
    filename: str = Field(..., description="The specific filename to search within. If omitted, all documents will be searched.")

@tool(args_schema=DocumentSearchArgs)
def search_user_documents(*, query: str, user_id: str, filename: str ) -> str:
    """
    Searches a user's private, indexed documents of a particular filename given by user to find context relevant to their query.
    search only by taking the filename.
    """
    # This improved log will clearly show if the filename is being passed
    print(f"Retrieving documents for user '{user_id}' with query '{query}' from filename: '{filename}'")
        
    try:
        collection = get_user_collection(user_id)
        
        if filename:
            results = collection.query(
                query_texts=[query],
                n_results=5,
                where={"source": "/tmp/"+filename}
            )
            print(results)
        else:
            results = collection.query(query_texts=[query], n_results=5)

        if not results or not results.get('documents') or not results['documents'][0]:
            return "No relevant information was found in the specified document."

        context = "\n---\n".join(results['documents'][0])
        return f"Found the following context from the user's documents:\n{context}"

    except Exception as e:
        print(f"Error retrieving from ChromaDB for user {user_id}: {e}")
        if "does not exist" in str(e):
             return "The user has not uploaded any documents yet."
        return "An error occurred while searching the documents."