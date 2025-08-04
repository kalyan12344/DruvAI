import chromadb

# FIX: Connect to the running server instead of accessing the files directly.
# This is more stable and avoids file permission issues.
chroma_client = chromadb.HttpClient(host="localhost", port=8000)

def get_user_collection(user_id: str):
    """
    Gets or creates a ChromaDB collection for a specific user.
    """
    collection_name = f"user_collection_{user_id}"
    return chroma_client.get_or_create_collection(name=collection_name)