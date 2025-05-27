import chromadb
from chromadb.config import Settings
import uuid

# Initialize the Chroma Client properly
memory_client = chromadb.HttpClient(host="chromadb", port=8000)

def create_memory_collection():
    try:
        collections = memory_client.list_collections()
        if any(c.name == "rune_memories" for c in collections):
            print("Memory collection already exists.")
        else:
            memory_client.create_collection(name="rune_memories")
            print("Memory collection created successfully.")
    except Exception as e:
        print(f"Failed to create or find memory collection: {e}")

def store_memory(content: str, metadata: dict = None):
    if metadata is None:
        metadata = {}

    memory_id = f"memory-{metadata.get('timestamp', str(uuid.uuid4()))}"

    try:
        collection = memory_client.get_collection(name="rune_memories")
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        print(f"Memory stored successfully: {memory_id}")
    except Exception as e:
        print(f"Failed to store memory: {e}")


def search_memory(query: str):
    return []
