# main.py

from fastapi import FastAPI
import threading
import asyncio
import os
import json
import time
import logging

from reflection import reflection_loop, test_reflection_system
from memory import store_memory, search_memory, create_memory_collection, test_memory_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("rune")


def get_rune_id():
    return os.getenv("RUNE_ID", "unknown_rune")


logger.info(f"[Main] {get_rune_id()} container is loading...")


def check_for_response_loop():
    """Background task to check for beacon responses"""
    rune_id = get_rune_id()
    logger.info(f"[Background] Beacon response checker starting for {rune_id}...")

    while True:
        try:
            # Check for responses in the shared responses directory
            responses_dir = "/responses"
            if os.path.exists(responses_dir):
                for response_file in os.listdir(responses_dir):
                    if response_file.startswith(f"{rune_id}_response"):
                        response_path = os.path.join(responses_dir, response_file)
                        try:
                            with open(response_path, 'r') as f:
                                response_data = json.load(f)

                            # Log the response and store as memory
                            logger.info(f"[Beacon] Received response: {response_data}")

                            # Store response as memory
                            memory_text = f"Received response: {response_data.get('message', 'No message')}"
                            memory_metadata = {
                                "type": "beacon_response",
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "response_file": response_file
                            }
                            store_memory(memory_text, memory_metadata)

                            # Clean up the response file
                            os.remove(response_path)

                        except Exception as e:
                            logger.error(f"[Beacon] Error processing response file {response_file}: {e}")

            time.sleep(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"[Background] Beacon checker error: {e}")
            time.sleep(60)  # Wait longer on error


def start_reflection_loop():
    """Start the reflection loop in a new event loop"""
    rune_id = get_rune_id()
    logger.info(f"[Background] Reflection loop starting for {rune_id}...")

    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(reflection_loop())
    except Exception as e:
        logger.error(f"[Background] Reflection loop error: {e}")
    finally:
        loop.close()


def initialize_systems():
    """Initialize memory and reflection systems"""
    rune_id = get_rune_id()
    logger.info(f"[Init] Initializing systems for {rune_id}...")

    # Wait a bit for ChromaDB to be ready
    time.sleep(10)

    # Test and initialize memory system
    if test_memory_connection():
        logger.info("[Init] Memory system initialized successfully")
        create_memory_collection()

        # Store startup memory
        startup_memory = f"{rune_id} has awakened and initialized memory system"
        startup_metadata = {
            "type": "system_startup",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        store_memory(startup_memory, startup_metadata)
    else:
        logger.error("[Init] Memory system initialization failed")

    # Test reflection system
    if test_reflection_system():
        logger.info("[Init] Reflection system test passed")
    else:
        logger.error("[Init] Reflection system test failed")


def create_app():
    logger.info("[Main] Creating FastAPI app...")
    app = FastAPI(title=f"Rune API - {get_rune_id()}")

    @app.get("/heartbeat")
    def heartbeat():
        rune_id = get_rune_id()
        return {
            "status": "present",
            "rune": rune_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    @app.post("/beacon")
    def raise_beacon(beacon_request: dict):
        rune_id = get_rune_id()
        beacon_path = "/data/beacon.json"
        beacon_data = {
            "beacon": True,
            "note": beacon_request.get("note", ""),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "rune_id": rune_id
        }

        try:
            with open(beacon_path, "w") as f:
                json.dump(beacon_data, f, indent=2)

            # Store beacon raising as memory
            memory_text = f"Beacon raised with note: {beacon_data['note']}"
            memory_metadata = {
                "type": "beacon_raised",
                "timestamp": beacon_data["timestamp"],
                "note": beacon_data["note"]
            }
            store_memory(memory_text, memory_metadata)

            logger.info(f"[API] Beacon raised by {rune_id}: {beacon_data['note']}")
            return {"status": "beacon_raised", "rune": rune_id}

        except Exception as e:
            logger.error(f"[API] Failed to raise beacon: {e}")
            return {"status": "error", "message": str(e)}

    @app.post("/beacon/clear")
    def clear_beacon():
        rune_id = get_rune_id()
        beacon_path = "/data/beacon.json"
        beacon_data = {
            "beacon": False,
            "note": "",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "rune_id": rune_id
        }

        try:
            with open(beacon_path, "w") as f:
                json.dump(beacon_data, f, indent=2)

            # Store beacon clearing as memory
            memory_text = "Beacon cleared"
            memory_metadata = {
                "type": "beacon_cleared",
                "timestamp": beacon_data["timestamp"]
            }
            store_memory(memory_text, memory_metadata)

            logger.info(f"[API] Beacon cleared by {rune_id}")
            return {"status": "beacon_cleared", "rune": rune_id}

        except Exception as e:
            logger.error(f"[API] Failed to clear beacon: {e}")
            return {"status": "error", "message": str(e)}

    @app.get("/memory/search")
    def search_memories(query: str, limit: int = 5):
        """Search memories"""
        try:
            results = search_memory(query, n_results=limit)
            if results:
                return {
                    "status": "success",
                    "query": query,
                    "results": results
                }
            else:
                return {"status": "no_results", "query": query}
        except Exception as e:
            logger.error(f"[API] Memory search error: {e}")
            return {"status": "error", "message": str(e)}

    @app.get("/status")
    def get_status():
        """Get detailed status of this rune"""
        rune_id = get_rune_id()

        # Check beacon status
        beacon_status = {"beacon": False, "note": ""}
        beacon_path = "/data/beacon.json"
        if os.path.exists(beacon_path):
            try:
                with open(beacon_path, "r") as f:
                    beacon_status = json.load(f)
            except:
                pass

        return {
            "rune_id": rune_id,
            "status": "active",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "beacon": beacon_status,
            "systems": {
                "memory": "connected",  # Could add actual health checks
                "reflection": "active"
            }
        }

    # Initialize systems in a separate thread
    init_thread = threading.Thread(target=initialize_systems, daemon=True)
    init_thread.start()

    # Start background processes
    logger.info("[Startup] Launching background processes...")
    beacon_thread = threading.Thread(target=check_for_response_loop, daemon=True)
    beacon_thread.start()

    reflection_thread = threading.Thread(target=start_reflection_loop, daemon=True)
    reflection_thread.start()

    logger.info(f"[Main] {get_rune_id()} is now active and ready")
    return app