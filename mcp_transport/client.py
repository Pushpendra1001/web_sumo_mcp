import requests
from sseclient import SSEClient
import threading
import json
import time

MCP_URL = "http://localhost:8000/mcp"

def listen_to_server():
    try:
        resp = requests.get(
            MCP_URL,
            stream=True,
            headers={"Accept": "text/event-stream"},
        )
        resp.raise_for_status()

        messages = SSEClient(resp)
        for msg in messages.events():
            
            try:
                data = json.loads(msg.data)
            except Exception:
                data = msg.data

            print("📥 From server:", data)
    except Exception as e:
        print("❌ SSE connection failed:", repr(e))
    
def send_request():
    payload = {
        "id": "1",
        "method": "say_hello",
        "params": {
            "name": "Pushpendra"
        }
    }

    res = requests.post(MCP_URL, json=payload)
    print("📤 POST response:", res.json())


threading.Thread(target=listen_to_server, daemon=True).start()


time.sleep(0.2)


send_request()

input("Press Enter to exit...")
