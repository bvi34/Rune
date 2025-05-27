import requests
import json

def inspect_memory(server="http://chromadb:8000", query="*"):
    try:
        query_payload = {
            "collection_name": "memory",
            "query_texts": [query],
            "n_results": 10
        }
        response = requests.post(f"{server}/api/v2/query", json=query_payload)
        if response.status_code == 200:
            results = response.json()
            memories = results.get("documents", [[]])[0]
            print("\n--- Recent Memories ---")
            for idx, memory in enumerate(memories, 1):
                print(f"{idx}. {memory}")
        else:
            print(f"Failed to query memory: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error querying memory: {e}")

if __name__ == "__main__":
    inspect_memory(server="http://localhost:8000", query="*")
