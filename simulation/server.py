import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# 1) Mount the "static" folder at /static
# Because server.py is in "simulation/" and the static folder is at "../static"
# we pass "directory='../static'" or "directory='static'" if it's at the same level.
app.mount("/static", StaticFiles(directory="../static"), name="static")

# Track active websocket connections
connected_clients = []

# Instantiate the traffic-lights logic
traffic_light_logic = TrafficLightLogic()

async def broadcast_state_to_clients(data_str: str):
    for ws in connected_clients:
        try:
            await ws.send_text(data_str)
        except:
            pass

traffic_light_logic.set_broadcast_callback(broadcast_state_to_clients)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    # Immediately send the current state
    await traffic_light_logic._broadcast_state()

    try:
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        connected_clients.remove(websocket)

@app.on_event("startup")
async def start_traffic_sequence():
    asyncio.create_task(traffic_light_logic.run_traffic_loop())

if __name__ == "__main__":
    # 2) Start the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
