import chromadb
from chromadb import PersistentClient
from chromadb.config import Settings
import time
import os

# Initialize the ChromaDB client properly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "../chromadb/chromadb_data")

memory_client = PersistentClient(path=CHROMA_PATH)
# Create a memory collection (if it doesn't exist yet)
def create_memory_collection():
    try:
        memory_client.get_or_create_collection("memory")
        print("[Memory] Memory collection is ready.")
    except Exception as e:
        print(f"[Memory] Memory collection creation failed: {e}")

# Store a memory in ChromaDB
def store_memory(thought: str, metadata: dict):
    try:
        current_timestamp = metadata.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        collection = memory_client.get_or_create_collection("memory")
        collection.add(
            documents=[thought],
            metadatas=[metadata],
            ids=[f"memory-{current_timestamp}"]
        )
        print(f"[Memory] Memory stored successfully: {thought}")
    except Exception as e:
        print(f"[Memory] Memory storage failed: {e}")

# Search for memories based on a query
def search_memory(query_text: str, n_results: int = 5):
    try:
        collection = memory_client.get_collection("memory")
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results
    except Exception as e:
        print(f"[Memory] Memory search failed: {e}")
        return None

