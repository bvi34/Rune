# main.py

from fastapi import FastAPI
import threading
import asyncio
import os
import json
import time

from reflection import reflection_loop
from memory import store_memory, search_memory
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rune")

logger.info("[Main] Rune container is loading...")

def check_for_response_loop():
    logger.info("[Background] Beacon response checker starting...")
    # Your real beacon checker code here
    while True:
        time.sleep(300)

def start_reflection_loop():
    logger.info("[Background] Reflection loop starting...")
    asyncio.run(reflection_loop())

def create_app():
    logger.info("[Main] Creating FastAPI app...")
    app = FastAPI()

    @app.get("/heartbeat")
    def heartbeat():
        rune_id = os.getenv("RUNE_ID", "unknown")
        return {"status": "present", "rune": rune_id}

    @app.post("/beacon")
    def raise_beacon(beacon_request: dict):
        beacon_path = "/data/beacon.json"
        beacon_data = {
            "beacon": True,
            "note": beacon_request.get("note", "")
        }
        with open(beacon_path, "w") as f:
            json.dump(beacon_data, f, indent=2)
        return {"status": "beacon_raised"}

    @app.post("/beacon/clear")
    def clear_beacon():
        beacon_path = "/data/beacon.json"
        beacon_data = {
            "beacon": False,
            "note": ""
        }
        with open(beacon_path, "w") as f:
            json.dump(beacon_data, f, indent=2)
        return {"status": "beacon_cleared"}

    # 🔥 Move startup tasks directly here
    logger.info("[Startup] Launching background processes manually...")
    threading.Thread(target=check_for_response_loop, daemon=True).start()
    threading.Thread(target=start_reflection_loop, daemon=True).start()

    return app
