import asyncio
import json
import random
import uvicorn
import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
from typing import Dict, Any
from trafficLights import TrafficLightLogic
from car_logic import Car

app = FastAPI()
db_path = "sqlite:///traffic_junction.db"
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
traffic_light_logic = TrafficLightLogic()
simulationSpeedMultiplier = 1.0  # Default multiplier

async def broadcast_to_all(data_str):
    for ws in connected_clients:
        try:
            await ws.send_text(data_str)
        except:
            pass

traffic_light_logic.set_broadcast_callback(broadcast_to_all)

###############################################################################
# Global: junction_data is set dynamically from the client, which sends canvas size
###############################################################################
junction_data = None

# Simulation time variables (in seconds)
simulationTime = 0
lastUpdateTime = None

# Simulation metrics in fast simulation/scoring
max_wait_time = 0      # max wait time (s)
total_wait_time = 0    # total wait time for all cars
wait_count = 0         # number of cars measured
max_queue_length = 0   # maximum number of cars in queue

async def update_simulation_time():
    global simulationTime, lastUpdateTime, simulationSpeedMultiplier
    while True:
        now = asyncio.get_event_loop().time()  # current time in seconds
        if lastUpdateTime is None:
            lastUpdateTime = now
        delta = now - lastUpdateTime
        lastUpdateTime = now
        # At speed 1: 1 real second adds 60 simulation seconds.
        simulationTime += delta * simulationSpeedMultiplier * 60
        
        # Calculate hours and minutes from simulationTime
        simulatedHours = int(simulationTime // 3600)
        simulatedMinutes = int((simulationTime % 3600) // 60)
        
        simulatedTimeStr = f"{simulatedHours}h {simulatedMinutes}m"
        
        message = {
            "simulatedTime": simulatedTimeStr,
            # ... include other simulation data if needed ...
        }
        await broadcast_to_all(json.dumps(message))
        await asyncio.sleep(1/60)


def create_junction_data(canvas_width, canvas_height, num_of_lanes=5, pixelWidthOfLane=20):
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
                    junction_data = create_junction_data(width, height)
                    print(f"Received canvasSize: {width}x{height}, junction_data set: {junction_data}")
                elif data.get("type") == "speedUpdate":
                    new_speed = data["speed"]
                    simulationSpeedMultiplier = new_speed  # update global multiplier
                    traffic_light_logic.simulationSpeedMultiplier = new_speed  # update in traffic lights
                    print("Updated simulation speed multiplier:", new_speed)
            except Exception as e:
                print("Error processing message:", e)
    except Exception as e:
        print("WebSocket error:", e)
    finally:
        connected_clients.remove(ws)

###############################################################################
# Spawn Rates (vehicles per minute) for each direction/turn type
###############################################################################
spawnRates: Dict[str, Any] = {}

@app.post("/update_spawn_rates")
def update_spawn_rates(data: Dict[str, Any]):
    """Receive spawn rates from app.py and update the dictionary."""
    global spawnRates
    spawnRates = data  # Store the latest spawn rates
    print("Spawn rates updated:", spawnRates)  # Debugging
    return {"message": "Spawn rates updated successfully"}

@app.get("/spawn_rates")
def get_spawn_rates():
    """Return the stored spawn rates."""
    return spawnRates if spawnRates else {"message": "No spawn rates available yet"}



###############################################################################
# Our global list of Car objects
###############################################################################
cars = []

def getLaneCandidates(numOfLanes):
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
    global cars, junction_data
    # Wait until junction_data is available.
    while junction_data is None:
        await asyncio.sleep(0.1)
    numOfLanes = junction_data["numOfLanes"]
    leftLane, rightLane, forwardLanes = getLaneCandidates(numOfLanes)
    while True:
        for direction in ["north", "east", "south", "west"]:
            for turnType in ["left", "forward", "right"]:
                base_vpm = spawnRates[direction][turnType]
                # Multiply base rate by simulationSpeedMultiplier so that, for example,
                # at multiplier 5, you spawn 5 times as many vehicles per real minute.
                effective_vpm = base_vpm * simulationSpeedMultiplier
                if effective_vpm <= 0:
                    continue
                # Probability per second: effective vehicles per minute / 60
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
                    new_car = Car(direction, lane, speed=2.0, turn_type=turnType, jd=junction_data)
                    new_car.spawn_time = simulationTime  # simulation time when car spawns
                    new_car.wait_recorded = False        # ensure wait time recorded only once
                    cars.append(new_car)
                    print(f"Spawned {direction} {turnType} car in lane {lane}")
        await asyncio.sleep(1)



def isOffCanvas(car):
    if (car.x < -200 or car.x > (junction_data["canvasWidth"] + 200) or
        car.y < -200 or car.y > (junction_data["canvasHeight"] + 200)):
        return True
    return False

async def update_car_loop():
    global cars, junction_data
    while True:
        main_lights = traffic_light_logic.trafficLightStates
        right_lights = traffic_light_logic.rightTurnLightStates
        for c in cars:
            base_speed = 2.0
            c.speed = base_speed * simulationSpeedMultiplier
            c.update(main_lights, right_lights, cars)
        cars = [c for c in cars if not isOffCanvas(c)]


        global max_wait_time, total_wait_time, wait_count, max_queue_length
        north_waiting_count = south_waiting_count = east_waiting_count = west_waiting_count = 0
        for c in cars:
            # ensure all cars have these attributes
            if not hasattr(c, 'spawn_time'):
                c.spawn_time = simulationTime
            if not hasattr(c, 'wait_recorded'):
                c.wait_recorded = False

            # if car has not been recorded as entered the junction
            if not c.wait_recorded:
                # check if car has entered junction
                if (junction_data["leftVertical"] <= c.x <= junction_data["rightVertical"] and
                    junction_data["topHorizontal"] <= c.y <= junction_data["bottomHorizontal"]):
                    wait_time = simulationTime - c.spawn_time
                    if wait_time > max_wait_time:
                        max_wait_time = wait_time
                    total_wait_time += wait_time
                    wait_count += 1
                    c.wait_recorded = True

            # count queueing cars in each arm
            if not c.wait_recorded:
                if c.direction == "north":
                    north_waiting_count += 1
                elif c.direction == "south":
                    south_waiting_count += 1
                elif c.direction == "east":
                    east_waiting_count += 1
                elif c.direction == "west":
                    west_waiting_count += 1

        max_queue_length = max(max_queue_length,north_waiting_count,south_waiting_count,east_waiting_count,west_waiting_count)


        data = {"cars": [c.to_dict() for c in cars]}
        await broadcast_to_all(json.dumps(data))
        await asyncio.sleep((1/60) / simulationSpeedMultiplier)


###############################################################################
# Used for fast simulation (calculating scores)
###############################################################################

async def run_fast_simulation(duration=10):
    # Run the simulation at a high speed for a given real-time duration (in seconds), and record scoring metrics
    global simulationSpeedMultiplier, max_wait_time, total_wait_time, wait_count, max_queue_length

    reset_simulation()

    # reset metrics
    max_wait_time = 0
    total_wait_time = 0
    wait_count = 0
    max_queue_length = 0

    # temporarily increase simulation speed
    old_multiplier = simulationSpeedMultiplier
    simulationSpeedMultiplier = 100.0  # set the high multiplier
    traffic_light_logic.simulationSpeedMultiplier = 100.0

    print(f"Running fast simulation for {duration} seconds with multiplier {simulationSpeedMultiplier}")
    await asyncio.sleep(duration)  # let simulation run quickly

    # restore original simulation speed
    simulationSpeedMultiplier = old_multiplier
    traffic_light_logic.simulationSpeedMultiplier = old_multiplier

    avg_wait_time = total_wait_time / wait_count if wait_count > 0 else 0
    metrics = {
        "max_wait_time": max_wait_time,
        "max_queue_length": max_queue_length,
        "avg_wait_time": avg_wait_time
    }
    print("Fast simulation metrics:", metrics)
    return metrics

# Expose endpoint to run fast simulation
@app.get("/simulate_fast")
async def simulate_fast_endpoint(duration: float = 10.0):
    # Run fast simulation for specified duration, return metrics
    metrics = await run_fast_simulation(duration)
    return metrics

# Resets the simulation
def reset_simulation():
    global simulationTime, lastUpdateTime, cars, spawnRates, traffic_light_logic
    simulationTime = 0
    lastUpdateTime = None
    cars = []
    # spawnRates = {} # We probably want to keep the spawn rates
    # Reinitialize the traffic lights
    traffic_light_logic = TrafficLightLogic()
    traffic_light_logic.set_broadcast_callback(broadcast_to_all)
    asyncio.create_task(traffic_light_logic.run_traffic_loop())

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(traffic_light_logic.run_traffic_loop())
    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
