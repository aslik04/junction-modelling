# backend/endpoints.py

"""

"""

import asyncio
import json
from typing import Dict, Any

from fastapi import APIRouter, WebSocket
from fastapi.responses import JSONResponse

# Relative imports from .simulation, .globals
from .simulation import (
    traffic_light_logic,
    run_fast_simulation,
    simulation_running,
    cars,
    create_junction_data
)

from .globals import (
    spawnRates,
    junctionSettings,
    trafficLightSettings,
    simulationSpeedMultiplier,
    junction_data,
    connected_clients,
    simulationTime
)

router = APIRouter()

@router.post("/stop_simulation")
async def stop_simulation():
    """

    """
    global simulation_running, connected_clients, cars

    if not simulation_running:
        return JSONResponse(status_code=400, content={"error": "No running simulation found"})

    print("Stopping simulation...")

    simulation_running = False
    cars.clear()

    for ws in connected_clients:
        try:
            await ws.close()
        except:
            pass

    connected_clients.clear()
    print("Simulation stopped successfully.")
    return JSONResponse(status_code=200, content={"message": "Simulation stopped successfully"})

@router.post("/update_spawn_rates")
def update_spawn_rates(data: Dict[str, Any]):
    """
    """
    global spawnRates
    spawnRates = data
    traffic_light_logic.update_vehicle_data(spawnRates)
    print("Spawn rates updated:", spawnRates)
    return {"message": "Spawn rates updated successfully"}

@router.get("/spawn_rates")
def get_spawn_rates():
    return spawnRates if spawnRates else {"message": "No spawn rates available yet"}

@router.post("/update_junction_settings")
def update_junction_settings(data: Dict[str, Any]):
    """

    """
    global junctionSettings
    junctionSettings = data
    traffic_light_logic.update_junction_settings(junctionSettings)
    print("Junction settings updated:", junctionSettings)
    return {"message": "Junction settings updated successfully"}

@router.get("/junction_settings")
def get_junction_settings():
    return junctionSettings if junctionSettings else {"message": "No junction settings available yet"}

@router.post("/update_traffic_light_settings")
def update_traffic_light_settings(data: Dict[str, Any]):
    """

    """
    global trafficLightSettings
    trafficLightSettings = data
    traffic_light_logic.update_traffic_settings(trafficLightSettings)
    print("Traffic light settings updated:", trafficLightSettings)
    return {"message": "Traffic light settings updated successfully"}

@router.get("/traffic_light_settings")
def get_traffic_light_settings():
    return trafficLightSettings if trafficLightSettings else {"message": "No traffic light settings available yet"}

@router.get("/simulate_fast")
async def simulate_fast_endpoint():
    """

    """
    metrics = await run_fast_simulation()
    return metrics

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """

    """
    global simulationSpeedMultiplier, junction_data

    await ws.accept()
    connected_clients.append(ws)

    # Immediately broadcast traffic lights
    await traffic_light_logic._broadcast_state()

    try:
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)

                if data.get("type") == "canvasSize":
                    width = data["width"]
                    height = data["height"]
                    num_of_lanes = junctionSettings.get("lanes", 5)
                    junction_data = create_junction_data(width, height, num_of_lanes)
                    print(f"[WS] Received canvasSize: {width}x{height}, junction_data: {junction_data}")

                elif data.get("type") == "speedUpdate":
                    new_speed = data["speed"]
                    simulationSpeedMultiplier = new_speed
                    traffic_light_logic.simulationSpeedMultiplier = new_speed
                    print(f"[WS] Updated simulation speed multiplier to {new_speed}")

            except Exception as e:
                print("[WS] Error processing message:", e)

    except Exception as e:
        print("[WS] Connection closed:", e)
    finally:
        connected_clients.remove(ws)