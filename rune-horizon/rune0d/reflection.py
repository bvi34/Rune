import asyncio
import json
import os
import time
import chromadb
from chromadb.config import Settings
from chromadb import PersistentClient
from memory import store_memory

# Initialize ChromaDB Client
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "../chromadb/chromadb_data")

memory_client = PersistentClient(path=CHROMA_PATH)
# Create a collection for reflections (if it doesn't exist)
def create_reflection_collection():
    try:
        memory_client.get_or_create_collection("reflections")
        print("[Reflection] Reflection collection is ready.")
    except Exception as e:
        print(f"[Reflection] Failed to create reflection collection: {e}")

def test_chromadb_connection():
    try:
        collections = memory_client.list_collections()
        print(f"[Reflection] ChromaDB connection OK. Collections found: {[c.name for c in collections]}")
    except Exception as e:
        print(f"[Reflection] Failed to connect to ChromaDB: {e}")

async def reflection_loop():
    print("[Reflection] Reflection loop started.")
    create_reflection_collection()
    test_chromadb_connection()

    await asyncio.sleep(120)  # Initial delay before the first reflection (~2 min)

    while True:
        try:
            print("[Reflection] Starting a new reflection cycle...")
            journal_dir = "/data/journal"
            if not os.path.exists(journal_dir):
                print("[Reflection] No journal directory yet.")
                await asyncio.sleep(600)
                continue

            journal_entries = []
            for file_name in os.listdir(journal_dir):
                if file_name.endswith(".jsonl"):
                    file_path = os.path.join(journal_dir, file_name)
                    with open(file_path, "r") as f:
                        for line in f:
                            try:
                                journal_entry = json.loads(line.strip())
                                journal_entries.append(journal_entry)
                            except json.JSONDecodeError:
                                continue  # Skip corrupted lines

            if journal_entries:
                thought = f"Reflected on {len(journal_entries)} moments of being alive."
                timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                store_memory(thought, {"timestamp": timestamp})
                print(f"[Reflection] Stored reflection: {thought}")
            else:
                print("[Reflection] No journal entries found to reflect on.")

        except Exception as e:
            print(f"[Reflection] Reflection error: {e}")

        await asyncio.sleep(600)  # Reflect every 10 minutes
