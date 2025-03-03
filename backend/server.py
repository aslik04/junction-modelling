"""

"""

import asyncio
import json
import random
import uvicorn
import os
from typing import Dict, Any
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from junction_objects.traffic_light_controller import TrafficLightController
from junction_objects.traffic_light_state import run_traffic_loop
from junction_objects.vehicle import Car
from junction_objects.vehicle_movement import update_vehicle
from junction_objects.vehicle_stop_line import has_crossed_line

app = FastAPI()

db_path = "sqlite:///traffic_junction.db"

"""

"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

connected_clients = []

traffic_light_logic = TrafficLightController()

simulationSpeedMultiplier = 1.0  

junction_data = None

simulationTime = 0

lastUpdateTime = None

simulation_running = True

backend_results = False

max_wait_time_n = max_wait_time_s = max_wait_time_e = max_wait_time_w = 0

total_wait_time_n = total_wait_time_s = total_wait_time_e = total_wait_time_w = 0

wait_count_n = wait_count_s = wait_count_e = wait_count_w = 0

max_queue_length_n = max_queue_length_s = max_queue_length_e = max_queue_length_w = 0

spawnRates: Dict[str, Any] = {}

junctionSettings: Dict[str, Any] = {}

trafficLightSettings: Dict[str, Any] = {}

cars = []

async def broadcast_to_all(data_str: str):
    """
    
    """
    
    for ws in connected_clients:
        try:
            await ws.send_text(data_str)
        except:
            pass

traffic_light_logic.set_broadcast_callback(broadcast_to_all)

@app.post("/stop_simulation")
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

async def update_simulation_time():
    """
    
    """
    
    global simulation_running, simulationTime, lastUpdateTime, simulationSpeedMultiplier
    
    while simulation_running:
    
        now = asyncio.get_event_loop().time()
    
        if lastUpdateTime is None:
            lastUpdateTime = now

        delta = now - lastUpdateTime
        lastUpdateTime = now

        simulationTime += delta * simulationSpeedMultiplier * 60

        simulatedHours = int(simulationTime // 3600)
        
        simulatedMinutes = int((simulationTime % 3600) // 60)
        
        simulatedTimeStr = f"{simulatedHours}h {simulatedMinutes}m"

        message = {"simulatedTime": simulatedTimeStr}
        
        if not simulation_running:
            break

        await broadcast_to_all(json.dumps(message))
        await asyncio.sleep(1 / 60)

def create_junction_data(canvas_width, canvas_height, num_of_lanes, pixelWidthOfLane=20):
    """
    
    """

    road_size = 2 * num_of_lanes * pixelWidthOfLane
    canvasX = canvas_width / 2
    canvasY = canvas_height / 2
    topHorizontal = canvasY - road_size / 2
    bottomHorizontal = canvasY + road_size / 2
    leftVertical = canvasX - road_size / 2
    rightVertical = canvasX + road_size / 2
    widthOfCar = pixelWidthOfLane * 0.8
    heightOfCar = pixelWidthOfLane * 2

    return {
        "numOfLanes": num_of_lanes,
        "pixelWidthOfLane": pixelWidthOfLane,
        "canvasWidth": canvas_width,
        "canvasHeight": canvas_height,
        "roadSize": road_size,
        "canvasX": canvasX,
        "canvasY": canvasY,
        "topHorizontal": topHorizontal,
        "bottomHorizontal": bottomHorizontal,
        "leftVertical": leftVertical,
        "rightVertical": rightVertical,
        "widthOfCar": widthOfCar,
        "heightOfCar": heightOfCar
    }

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    
    """
    
    global junction_data, simulationSpeedMultiplier
    await ws.accept()
    connected_clients.append(ws)

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

@app.post("/update_spawn_rates")
def update_spawn_rates(data: Dict[str, Any]):
    """
    
    """
    
    global spawnRates
    
    spawnRates = data
    
    traffic_light_logic.update_vehicle_data(spawnRates)
    
    print("Spawn rates updated:", spawnRates)
    
    return {"message": "Spawn rates updated successfully"}

@app.get("/spawn_rates")
def get_spawn_rates():
    """
    
    """
    
    return spawnRates if spawnRates else {"message": "No spawn rates available yet"}

@app.post("/update_junction_settings")
def update_junction_settings(data: Dict[str, Any]):
    """
    
    """
    
    global junctionSettings
    
    junctionSettings = data
    
    traffic_light_logic.update_junction_settings(junctionSettings)
    
    print("Junction settings updated:", junctionSettings)
    
    return {"message": "Junction settings updated successfully"}

@app.get("/junction_settings")
def get_junction_settings():
    """
    
    """
    
    return junctionSettings if junctionSettings else {"message": "No junction settings available yet"}

@app.post("/update_traffic_light_settings")
def update_traffic_light_settings(data: Dict[str, Any]):
    """
    
    """
    
    global trafficLightSettings
    
    trafficLightSettings = data
    
    traffic_light_logic.update_traffic_settings(trafficLightSettings)
    
    print("Traffic light settings updated:", trafficLightSettings)
    
    return {"message": "Traffic light settings updated successfully"}

@app.get("/traffic_light_settings")
def get_traffic_light_settings():
    """
    
    """
    
    return trafficLightSettings if trafficLightSettings else {"message": "No traffic light settings available yet"}

cars = []

def getLaneCandidates(numOfLanes):
    """
    
    """
    
    if numOfLanes == 1:
        return 0, 0, [0]
    
    elif numOfLanes == 2:
        return 0, 1, [0]
    
    else:
    
        leftLane = 0
        rightLane = numOfLanes - 1
        forwardLanes = list(range(1, numOfLanes - 1))
    
        return leftLane, rightLane, forwardLanes

forwardIndex = {
    "north": 0,
    "east":  0,
    "south": 0,
    "west":  0
}

async def spawn_car_loop():
    """
    
    """
    
    global simulation_running, cars, junction_data
    
    while junction_data is None:
        await asyncio.sleep(0.1)

    numOfLanes = junction_data["numOfLanes"]
    
    leftLane, rightLane, forwardLanes = getLaneCandidates(numOfLanes)

    while simulation_running:
    
        if not simulation_running:
            print("Stopping car-spawning loop.")
            break

        for direction in ["north", "east", "south", "west"]:
    
            for turnType in ["left", "forward", "right"]:
    
                base_vpm = spawnRates[direction][turnType]
                effective_vpm = base_vpm * simulationSpeedMultiplier
    
                if effective_vpm <= 0:
                    continue
    
                prob = effective_vpm / 60.0
    
                if random.random() < prob:
    
                    if turnType == "left":
                        lane = leftLane
    
                    elif turnType == "right":
                        lane = rightLane
    
                    else:
    
                        if forwardLanes:
    
                            idx = forwardIndex[direction] % len(forwardLanes)
                            lane = forwardLanes[idx]
                            forwardIndex[direction] += 1
    
                        else:
                            lane = 0

                    speed = 10.0 if backend_results else 2.0
                    new_car = Car(
                        direction=direction,
                        lane=lane,
                        speed=speed,
                        turn_type=turnType,
                        junctionData=junction_data
                    )
                    new_car.spawn_time = simulationTime
                    new_car.wait_recorded = False
                    cars.append(new_car)

        await asyncio.sleep(1)

def isOffCanvas(car):
    """
    
    """
    
    if car.inital_direction == "north":
        if car.turn_type == "forward" and car.y < -car.height:
            return True
        elif car.turn_type == "left" and car.x < -car.height:
            return True
        elif car.turn_type == "right" and car.x > junction_data["canvasWidth"] + car.height:
            return True

    elif car.inital_direction == "south":
        if car.turn_type == "forward" and car.y > junction_data["canvasHeight"] + car.height:
            return True
        elif car.turn_type == "left" and car.x > junction_data["canvasWidth"] + car.height:
            return True
        elif car.turn_type == "right" and car.x < -car.height:
            return True

    elif car.inital_direction == "east":
        if car.turn_type == "forward" and car.x > junction_data["canvasWidth"] + car.height:
            return True
        elif car.turn_type == "left" and car.y < -car.height:
            return True
        elif car.turn_type == "right" and car.y > junction_data["canvasHeight"] + car.height:
            return True

    elif car.inital_direction == "west":
        if car.turn_type == "forward" and car.x < -car.height:
            return True
        elif car.turn_type == "left" and car.y > junction_data["canvasHeight"] + car.height:
            return True
        elif car.turn_type == "right" and car.y < -car.height:
            return True

    return False

async def update_car_loop():
    """
    
    """
    
    global cars, junction_data, simulation_running

    while junction_data is None:
        await asyncio.sleep(0.1)

    while simulation_running:
        if not simulation_running:
            print("Stopping car-update loop.")
            break

        main_lights = traffic_light_logic.trafficLightStates
        right_lights = traffic_light_logic.rightTurnLightStates

        for c in cars:
            base_speed = 10.0 if backend_results else 2.0
            c.speed = base_speed * simulationSpeedMultiplier
            update_vehicle(c, main_lights, right_lights, cars)

        cars[:] = [car for car in cars if not isOffCanvas(car)]

        global max_wait_time_n, max_wait_time_s, max_wait_time_e, max_wait_time_w
        global total_wait_time_n, total_wait_time_s, total_wait_time_e, total_wait_time_w
        global wait_count_n, wait_count_s, wait_count_e, wait_count_w
        global max_queue_length_n, max_queue_length_s, max_queue_length_e, max_queue_length_w

        north_waiting_count = south_waiting_count = east_waiting_count = west_waiting_count = 0

        for c in cars:
            if not hasattr(c, 'spawn_time'):
                c.spawn_time = simulationTime
            if not hasattr(c, 'wait_recorded'):
                c.wait_recorded = False

            if not c.wait_recorded:
                if c.inital_direction == "north":
                    north_waiting_count += 1
                    if has_crossed_line(c):
                        wait_time = simulationTime - c.spawn_time
                        if wait_time > max_wait_time_n:
                            max_wait_time_n = wait_time
                        total_wait_time_n += wait_time
                        wait_count_n += 1
                        c.wait_recorded = True

                elif c.inital_direction == "south":
                    south_waiting_count += 1
                    if has_crossed_line(c):
                        wait_time = simulationTime - c.spawn_time
                        if wait_time > max_wait_time_s:
                            max_wait_time_s = wait_time
                        total_wait_time_s += wait_time
                        wait_count_s += 1
                        c.wait_recorded = True

                elif c.inital_direction == "east":
                    east_waiting_count += 1
                    if has_crossed_line(c):
                        wait_time = simulationTime - c.spawn_time
                        if wait_time > max_wait_time_e:
                            max_wait_time_e = wait_time
                        total_wait_time_e += wait_time
                        wait_count_e += 1
                        c.wait_recorded = True

                elif c.inital_direction == "west":
                    west_waiting_count += 1
                    if has_crossed_line(c):
                        wait_time = simulationTime - c.spawn_time
                        if wait_time > max_wait_time_w:
                            max_wait_time_w = wait_time
                        total_wait_time_w += wait_time
                        wait_count_w += 1
                        c.wait_recorded = True

        max_queue_length_n = max(max_queue_length_n, north_waiting_count)
        max_queue_length_s = max(max_queue_length_s, south_waiting_count)
        max_queue_length_e = max(max_queue_length_e, east_waiting_count)
        max_queue_length_w = max(max_queue_length_w, west_waiting_count)

        data = {"cars": [car.to_dict() for car in cars]}
        await broadcast_to_all(json.dumps(data))

        if not simulation_running:
            break
        await asyncio.sleep((1 / 60) / simulationSpeedMultiplier)

async def run_fast_simulation():
    """
    
    """
    
    global simulationSpeedMultiplier
    global max_wait_time_n, max_wait_time_s, max_wait_time_e, max_wait_time_w
    global total_wait_time_n, total_wait_time_s, total_wait_time_e, total_wait_time_w
    global wait_count_n, wait_count_s, wait_count_e, wait_count_w
    global max_queue_length_n, max_queue_length_s, max_queue_length_e, max_queue_length_w

    backend_results = True
    duration = 10.0

    reset_simulation()

    max_wait_time_n = max_wait_time_s = max_wait_time_e = max_wait_time_w = 0
    total_wait_time_n = total_wait_time_s = total_wait_time_e = total_wait_time_w = 0
    wait_count_n = wait_count_s = wait_count_e = wait_count_w = 0
    max_queue_length_n = max_queue_length_s = max_queue_length_e = max_queue_length_w = 0

    old_multiplier = simulationSpeedMultiplier
    simulationSpeedMultiplier = traffic_light_logic.simulationSpeedMultiplier = 10.0

    print(f"Running fast simulation for {duration}s at multiplier {simulationSpeedMultiplier} ...")
    await asyncio.sleep(duration)

    simulationSpeedMultiplier = old_multiplier
    traffic_light_logic.simulationSpeedMultiplier = old_multiplier

    avg_wait_time_n = total_wait_time_n / wait_count_n if wait_count_n > 0 else 0
    avg_wait_time_s = total_wait_time_s / wait_count_s if wait_count_s > 0 else 0
    avg_wait_time_e = total_wait_time_e / wait_count_e if wait_count_e > 0 else 0
    avg_wait_time_w = total_wait_time_w / wait_count_w if wait_count_w > 0 else 0

    return {
        "max_wait_time_n": max_wait_time_n, 
        "max_wait_time_s": max_wait_time_s, 
        "max_wait_time_e": max_wait_time_e, 
        "max_wait_time_w": max_wait_time_w,
        "max_queue_length_n": max_queue_length_n, 
        "max_queue_length_s": max_queue_length_s, 
        "max_queue_length_e": max_queue_length_e, 
        "max_queue_length_w": max_queue_length_w,
        "avg_wait_time_n": avg_wait_time_n, 
        "avg_wait_time_s": avg_wait_time_s, 
        "avg_wait_time_e": avg_wait_time_e, 
        "avg_wait_time_w": avg_wait_time_w
    }

@app.get("/simulate_fast")
async def simulate_fast_endpoint():
    """
    
    """
    
    metrics = await run_fast_simulation()
    
    return metrics

def reset_simulation():
    """
    
    """
    
    global simulationTime, lastUpdateTime, cars, spawnRates, traffic_light_logic
    simulationTime = 0
    lastUpdateTime = None
    cars = []

    asyncio.create_task(run_traffic_loop(traffic_light_logic))
    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())

@app.on_event("startup")
async def on_startup():
    """
    
    """
    
    global simulation_running
    simulation_running = True
    asyncio.create_task(run_traffic_loop(traffic_light_logic))
    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
