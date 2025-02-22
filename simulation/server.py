import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from trafficLights import TrafficLightLogic

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo/dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track active websocket connections
connected_clients = []

# Instantiate the traffic-lights logic
traffic_light_logic = TrafficLightLogic()

async def broadcast_state_to_clients(data_str: str):
    """
    Send the given JSON string to all connected websocket clients.
    """
    for ws in connected_clients:
        try:
            await ws.send_text(data_str)
        except:
            # If we fail to send, we could remove or ignore the client, etc.
            pass

# Give our logic a reference to the broadcast function
traffic_light_logic.set_broadcast_callback(broadcast_state_to_clients)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    # Immediately send the current state
    await traffic_light_logic._broadcast_state()

    try:
        while True:
            # If the client sends something (e.g., to change timings) handle it here
            await websocket.receive_text()
    except:
        pass
    finally:
        connected_clients.remove(websocket)

@app.on_event("startup")
async def start_traffic_sequence():
    asyncio.create_task(traffic_light_logic.run_traffic_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
