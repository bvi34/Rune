import chromadb
from chromadb import HttpClient
from chromadb.config import Settings
import time
import os
import logging

logger = logging.getLogger("rune.memory")

# Connect to ChromaDB service running in Docker
# Use the container name 'chromadb' and port 8000 (internal port)
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "chromadb")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))

try:
    memory_client = HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
    logger.info(f"[Memory] Connected to ChromaDB at {CHROMADB_HOST}:{CHROMADB_PORT}")
except Exception as e:
    logger.error(f"[Memory] Failed to connect to ChromaDB: {e}")
    memory_client = None


def ensure_chromadb_connection():
    """Ensure ChromaDB connection is available"""
    global memory_client
    if memory_client is None:
        try:
            memory_client = HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
            logger.info("[Memory] Reconnected to ChromaDB")
            return True
        except Exception as e:
            logger.error(f"[Memory] Failed to reconnect to ChromaDB: {e}")
            return False
    return True


def get_rune_id():
    """Get the current rune's ID from environment"""
    return os.getenv("RUNE_ID", "unknown_rune")


def create_memory_collection():
    """Create or get the memory collection for this rune"""
    if not ensure_chromadb_connection():
        return False

    try:
        rune_id = get_rune_id()
        collection_name = f"memory_{rune_id.lower()}"

        collection = memory_client.get_or_create_collection(collection_name)
        logger.info(f"[Memory] Memory collection '{collection_name}' is ready")
        return True
    except Exception as e:
        logger.error(f"[Memory] Memory collection creation failed: {e}")
        return False


def store_memory(thought: str, metadata: dict = None):
    """Store a memory in ChromaDB"""
    if not ensure_chromadb_connection():
        logger.error("[Memory] Cannot store memory - no ChromaDB connection")
        return False

    try:
        if metadata is None:
            metadata = {}

        rune_id = get_rune_id()
        collection_name = f"memory_{rune_id.lower()}"

        # Add rune_id to metadata
        metadata["rune_id"] = rune_id
        metadata["stored_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Get timestamp for ID
        timestamp = metadata.get("timestamp", metadata["stored_at"])
        memory_id = f"memory-{rune_id}-{int(time.time())}-{hash(thought) % 10000}"

        collection = memory_client.get_or_create_collection(collection_name)
        collection.add(
            documents=[thought],
            metadatas=[metadata],
            ids=[memory_id]
        )

        logger.info(f"[Memory] Stored memory for {rune_id}: {thought[:50]}...")
        return True

    except Exception as e:
        logger.error(f"[Memory] Memory storage failed: {e}")
        return False


def search_memory(query_text: str, n_results: int = 5):
    """Search for memories based on a query"""
    if not ensure_chromadb_connection():
        logger.error("[Memory] Cannot search memory - no ChromaDB connection")
        return None

    try:
        rune_id = get_rune_id()
        collection_name = f"memory_{rune_id.lower()}"

        collection = memory_client.get_collection(collection_name)
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

        logger.info(
            f"[Memory] Found {len(results['documents'][0]) if results['documents'] else 0} memories for query: {query_text}")
        return results

    except Exception as e:
        logger.error(f"[Memory] Memory search failed: {e}")
        return None


def get_all_memories(limit: int = 100):
    """Get all memories for this rune (for reflection purposes)"""
    if not ensure_chromadb_connection():
        logger.error("[Memory] Cannot get memories - no ChromaDB connection")
        return []

    try:
        rune_id = get_rune_id()
        collection_name = f"memory_{rune_id.lower()}"

        collection = memory_client.get_collection(collection_name)

        # Get all items (ChromaDB doesn't have a direct "get all" with limit, so we'll use get())
        results = collection.get(limit=limit)

        memories = []
        if results and results.get('documents'):
            for i, doc in enumerate(results['documents']):
                memory = {
                    'document': doc,
                    'metadata': results['metadatas'][i] if results.get('metadatas') else {},
                    'id': results['ids'][i] if results.get('ids') else None
                }
                memories.append(memory)

        logger.info(f"[Memory] Retrieved {len(memories)} memories for {rune_id}")
        return memories

    except Exception as e:
        logger.error(f"[Memory] Failed to get all memories: {e}")
        return []


def test_memory_connection():
    """Test the memory system"""
    logger.info("[Memory] Testing memory connection...")

    if not ensure_chromadb_connection():
        return False

    try:
        # Test collection creation
        if not create_memory_collection():
            return False

        # Test storing a memory
        test_thought = "Memory system test - connection working"
        test_metadata = {"type": "system_test", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

        if not store_memory(test_thought, test_metadata):
            return False

        # Test searching
        results = search_memory("test", n_results=1)
        if results is None:
            return False

        logger.info("[Memory] Memory system test passed!")
        return True

    except Exception as e:
        logger.error(f"[Memory] Memory system test failed: {e}")
        return False