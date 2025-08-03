import chromadb

# This initializes a persistent client that saves data to a local folder
# named 'chroma_data' in your project directory.
chroma_client = chromadb.PersistentClient(path="./chroma_data")

def get_user_collection(user_id: str):
    """
    Gets or creates a ChromaDB collection for a specific user to keep data separate.
    """
    collection_name = f"user_collection_{user_id}"
    return chroma_client.get_or_create_collection(name=collection_name)