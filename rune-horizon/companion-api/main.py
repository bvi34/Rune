from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
import os
import json
import hmac
import hashlib

SHARED_SECRET=bytes.fromhex("43dcfe2513f76b10cd10a9ac3d82cfbb281eeba7038615238a2f46c4c9661d2a")
app = FastAPI()

class BeaconRequest(BaseModel):
    note: str = ""

# List of Rune endpoints (use localhost ports!)
RUNES = {
    "Rune00": "http://localhost:6000",
    "Rune0A": "http://localhost:6001",
    "Rune0B": "http://localhost:6002",
    "Rune0C": "http://localhost:6003",
    "Rune0D": "http://localhost:6004",
}

# Path where Companion stores optional human responses to Runes
RESPONSES_DIR = "/responses"

# Ensure response folder exists
os.makedirs(RESPONSES_DIR, exist_ok=True)

class ResponseMessage(BaseModel):
    message: str

@app.get("/heartbeat")
def check_heartbeats():
    """
    Check heartbeat of all Runes and report their status.
    """
    status_report = {}
    for rune, url in RUNES.items():
        try:
            response = requests.get(f"{url}/heartbeat", timeout=2)
            if response.status_code == 200:
                data = response.json()
                status_report[rune] = {"status": "present", "id": data.get("rune", "unknown")}
            else:
                status_report[rune] = {"status": "error", "id": "unknown"}
        except Exception as e:
            status_report[rune] = {"status": "unreachable", "id": "unknown"}
    return status_report

@app.get("/beacons")
def check_beacons():
    """
    Check if any Rune has raised a beacon asking for help.
    """
    beacon_report = {}
    for rune in RUNES.keys():
        beacon_file = f"/data/{rune.lower()}/beacon.json"
        if os.path.exists(beacon_file):
            with open(beacon_file, "r") as f:
                data = json.load(f)
            beacon_report[rune] = {
                "beacon": data.get("beacon", False),
                "note": data.get("note", "")
            }
        else:
            beacon_report[rune] = {"beacon": False, "note": ""}
    return beacon_report

@app.post("/respond/{rune_id}")
def respond_to_beacon(rune_id: str, response: ResponseMessage):
    """
    Save a response message for a specific Rune to read later.
    """
    filepath = os.path.join(RESPONSES_DIR, f"{rune_id}.json")
    with open(filepath, "w") as f:
        json.dump({"message": response.message}, f, indent=2)
    return {"status": "saved", "rune": rune_id}
import requests

@app.get("/memories")
def get_memories():
    try:
        query_payload = {
            "collection_name": "memory",
            "query_texts": ["*"],
            "n_results": 10
        }
        response = requests.post("http://localhost:8000/api/v2/query", json=query_payload)
        
        if response.status_code == 200:
            results = response.json()
            documents = results.get("documents", [[]])[0]
            return {"memories": documents}
        else:
            return {"error": f"Failed to fetch memories: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

