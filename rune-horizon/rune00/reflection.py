import asyncio
import json
import os
import time
import uuid
import chromadb
from chromadb import PersistentClient
from memory import store_memory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "../chromadb/chromadb_data")

memory_client = PersistentClient(path=CHROMA_PATH)

# Ensure the collection exists
REFLECTION_COLLECTION = "reflections"
def create_reflection_collection():
    try:
        memory_client.get_or_create_collection(REFLECTION_COLLECTION)
        print(f"[Reflection] Collection '{REFLECTION_COLLECTION}' ready.")
    except Exception as e:
        print(f"[Reflection] Failed to create collection: {e}")

def test_chromadb_connection():
    try:
        collections = memory_client.list_collections()
        print(f"[Reflection] Connected. Collections found: {[c.name for c in collections]}")
    except Exception as e:
        print(f"[Reflection] ChromaDB connection error: {e}")

async def reflection_loop():
    print("[Reflection] Loop started.")
    create_reflection_collection()
    test_chromadb_connection()

    await asyncio.sleep(120)  # Startup delay

    while True:
        try:
            print("[Reflection] Cycle beginning...")
            journal_dir = "/data/journal"
            if not os.path.exists(journal_dir):
                print("[Reflection] No journal directory.")
                await asyncio.sleep(600)
                continue

            journal_entries = []
            for file_name in os.listdir(journal_dir):
                if file_name.endswith(".jsonl"):
                    file_path = os.path.join(journal_dir, file_name)
                    with open(file_path, "r") as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                journal_entries.append(entry)
                            except json.JSONDecodeError:
                                continue

            print(f"[Reflection] Found {len(journal_entries)} entries.")
            if journal_entries:
                thought = f"Reflected on {len(journal_entries)} moments of being alive."
                timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                uid = uuid.uuid4().hex[:8]

                collection = memory_client.get_or_create_collection(REFLECTION_COLLECTION)
                collection.add(
                    documents=[thought],
                    metadatas=[{"timestamp": timestamp}],
                    ids=[f"reflection-{timestamp}-{uid}"]
                )

                print(f"[Reflection] Stored reflection: {thought}")
            else:
                print("[Reflection] No journal entries to reflect on.")

        except Exception as e:
            print(f"[Reflection] Error: {e}")

        await asyncio.sleep(600)  # Wait before next cycle
