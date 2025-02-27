import asyncio
import json
import random
import uvicorn
import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse 
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
simulation_running = True

backend_results = False 

# Simulation metrics in fast simulation/scoring
max_wait_time_n = max_wait_time_s = max_wait_time_e = max_wait_time_w = 0      # max wait time (s)
total_wait_time_n = total_wait_time_s = total_wait_time_e = total_wait_time_w = 0    # total wait time for all cars
wait_count_n = wait_count_s = wait_count_e = wait_count_w = 0         # number of cars measured
max_queue_length_n = max_queue_length_s = max_queue_length_e = max_queue_length_w = 0   # maximum number of cars in queue

@app.post("/stop_simulation")
async def stop_simulation():
    """
    Stop the running simulation properly.
    """
    global simulation_running, connected_clients, cars

    if not simulation_running:
        return JSONResponse(status_code=400, content={"error": "No running simulation found"})
    print("Stopping sim")
    simulation_running = False
    cars.clear()
    for ws in connected_clients:
        try:
            await ws.close()
        except:
            pass  # Ignore errors
    connected_clients.clear()
    print("Simulation successfully stopped.")
    return JSONResponse(status_code=200, content={"message": "Simulation stopped successfully"})


async def update_simulation_time():
    global simulation_running, simulationTime, lastUpdateTime, simulationSpeedMultiplier
    while simulation_running:
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
        if not simulation_running:
            break
        await broadcast_to_all(json.dumps(message))
        await asyncio.sleep(1/60)


def create_junction_data(canvas_width, canvas_height, num_of_lanes, pixelWidthOfLane=20):
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
                    num_of_lanes = junctionSettings.get("lanes", 5)
                    junction_data = create_junction_data(width, height, num_of_lanes)
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
    # Pass the new vehicle data to the traffic light logic
    traffic_light_logic.update_vehicle_data(spawnRates)
    print("Spawn rates updated:", spawnRates)  # Debugging
    return {"message": "Spawn rates updated successfully"}

@app.get("/spawn_rates")
def get_spawn_rates():
    """Return the stored spawn rates."""
    return spawnRates if spawnRates else {"message": "No spawn rates available yet"}


###############################################################################
# Junction Settings
###############################################################################
junctionSettings: Dict[str, Any] = {}

@app.post("/update_junction_settings")
def update_junction_settings(data: Dict[str, Any]):
    global junctionSettings
    junctionSettings = data  # Store the latest junction settings
    traffic_light_logic.update_junction_settings(junctionSettings)
    print("Junction settings updated:", junctionSettings)
    return {"message": "Junction settings updated successfully"}

@app.get("/junction_settings")
def get_junction_settings():
    return junctionSettings if junctionSettings else {"message": "No junction settings available yet"}


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
    global simulation_running, cars, junction_data
    # Wait until junction_data is available.
    while junction_data is None:
        await asyncio.sleep(0.1)
    numOfLanes = junction_data["numOfLanes"]
    leftLane, rightLane, forwardLanes = getLaneCandidates(numOfLanes)
    while simulation_running:
        if not simulation_running:
            print("Stopping car spawning loop")
            break
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
                    if backend_results:
                        speed = 10.0
                    else:
                        speed = 2.0
                    new_car = Car(direction, lane, speed, turn_type=turnType, jd=junction_data)
                    new_car.spawn_time = simulationTime  # simulation time when car spawns
                    new_car.wait_recorded = False        # ensure wait time recorded only once
                    cars.append(new_car)
        if not simulation_running: 
            break
        await asyncio.sleep(1)



def isOffCanvas(car):
    # Check based on the direction of travel
    if car.initial_direction == "north":
        # Northbound cars leave at the top.
        if car.turn_type == "forward" and car.y < - car.height:
            return True
        elif car.turn_type == "left" and car.x < -car.height:
            return True
        elif car.turn_type == "right" and car.x > junction_data["canvasWidth"] + car.height:
            return True
    elif car.initial_direction == "south":
        # Southbound cars leave at the bottom.
        if car.turn_type == "forward" and car.y > junction_data["canvasHeight"] + car.height:
            return True
        elif car.turn_type == "left" and car.x > junction_data["canvasWidth"] + car.height:
            return True
        elif car.turn_type == "right" and car.x < -car.height:
            return True
    elif car.initial_direction == "east":
        # Eastbound cars leave on the right.
        if car.turn_type == "forward" and car.x > junction_data["canvasWidth"] + car.height:
            return True
        elif car.turn_type == "left" and car.y < -car.height:
            return True
        elif car.turn_type == "right" and car.y > junction_data["canvasHeight"] + car.height:
            return True
    elif car.initial_direction == "west":
        # Westbound cars leave on the left.
        if car.turn_type == "forward" and car.x < -car.height:
            return True
        elif car.turn_type == "left" and car.y > junction_data["canvasHeight"] + car.height:
            return True
        elif car.turn_type == "right" and car.y < -car.height:
            return True
    return False

async def update_car_loop():
    global cars, junction_data, simulation_running

    while junction_data is None: # Wait until junction_data is available.
        await asyncio.sleep(0.1)

    while simulation_running:
        if not simulation_running:
            print("Stopping car update loop")
            break 
        main_lights = traffic_light_logic.trafficLightStates
        right_lights = traffic_light_logic.rightTurnLightStates
        for c in cars:
            if backend_results:
                base_speed = 10.0
            else:
                base_speed = 2.0
            c.speed = base_speed * simulationSpeedMultiplier
            c.update(main_lights, right_lights, cars)
        cars = [c for c in cars if not isOffCanvas(c)]


        global max_wait_time_n, max_wait_time_s, max_wait_time_e, max_wait_time_w
        global total_wait_time_n, total_wait_time_s, total_wait_time_e, total_wait_time_w
        global wait_count_n, wait_count_s, wait_count_e, wait_count_w
        global max_queue_length_n, max_queue_length_s, max_queue_length_e, max_queue_length_w
        north_waiting_count = south_waiting_count = east_waiting_count = west_waiting_count = 0

        for c in cars:
            """ if c.direction == "east":
                #print("big error") """
            # ensure all cars have these attributes
            if not hasattr(c, 'spawn_time'):
                c.spawn_time = simulationTime
            if not hasattr(c, 'wait_recorded'):
                c.wait_recorded = False

            # if car has not been recorded as entered the junction
            if not c.wait_recorded:
                if c.initial_direction == "north":
                    north_waiting_count += 1
                    # check if car has entered junction
                    if (c.is_beyond_line()):
                        wait_time = simulationTime - c.spawn_time
                        if wait_time > max_wait_time_n:
                            max_wait_time_n = wait_time
                        total_wait_time_n += wait_time
                        wait_count_n += 1
                        c.wait_recorded = True
                elif c.initial_direction == "south":
                    south_waiting_count += 1
                    # check if car has entered junction
                    if (c.is_beyond_line()):
                        wait_time = simulationTime - c.spawn_time
                        if wait_time > max_wait_time_s:
                            max_wait_time_s = wait_time
                        total_wait_time_s += wait_time
                        wait_count_s += 1
                        c.wait_recorded = True
                elif c.initial_direction == "east":
                    east_waiting_count += 1
                    # check if car has entered junction
                    if (c.is_beyond_line()):
                        wait_time = simulationTime - c.spawn_time
                        if wait_time > max_wait_time_e:
                            max_wait_time_e = wait_time
                        total_wait_time_e += wait_time
                        wait_count_e += 1
                        c.wait_recorded = True
                        print("recording east uncorrectly")
                        print(c.direction)
                elif c.initial_direction == "west":
                    west_waiting_count += 1
                    # check if car has entered junction
                    if (c.is_beyond_line()):
                        wait_time = simulationTime - c.spawn_time
                        if wait_time > max_wait_time_w:
                            max_wait_time_w = wait_time
                        total_wait_time_w += wait_time
                        wait_count_w += 1
                        c.wait_recorded = True

        print("north_waiting_count: ", north_waiting_count)
        print("south_waiting_count: ", south_waiting_count)
        print("east_waiting_count: ", east_waiting_count)
        print("west_waiting_count: ", west_waiting_count)

        max_queue_length_n = max(max_queue_length_n,north_waiting_count)
        max_queue_length_s = max(max_queue_length_s,south_waiting_count)
        max_queue_length_e = max(max_queue_length_e,east_waiting_count)
        max_queue_length_w = max(max_queue_length_w,west_waiting_count)#

        print("max_queue_length_n: ", max_queue_length_n)
        print("max_queue_length_s: ", max_queue_length_s)
        print("max_queue_length_e: ", max_queue_length_e)
        print("max_queue_length_w: ", max_queue_length_w)


        data = {"cars": [c.to_dict() for c in cars]}
        await broadcast_to_all(json.dumps(data))
        if not simulation_running:
            break
        await asyncio.sleep((1/60) / simulationSpeedMultiplier)


###############################################################################
# Used for fast simulation (calculating scores)
###############################################################################

async def run_fast_simulation():
    # Run the simulation at a high speed for a given real-time duration (in seconds), and record scoring metrics
    global simulationSpeedMultiplier
    global max_wait_time_n, max_wait_time_s, max_wait_time_e, max_wait_time_w
    global total_wait_time_n, total_wait_time_s, total_wait_time_e, total_wait_time_w
    global wait_count_n, wait_count_s, wait_count_e, wait_count_w
    global max_queue_length_n, max_queue_length_s, max_queue_length_e, max_queue_length_w

    backend_results = True

    duration = 10.0

    reset_simulation()

    print(cars)

    # reset metrics
    max_wait_time_n = max_wait_time_s = max_wait_time_e = max_wait_time_w = 0
    total_wait_time_n = total_wait_time_s = total_wait_time_e = total_wait_time_w = 0
    wait_count_n = wait_count_s = wait_count_e = wait_count_w = 0
    max_queue_length_n = max_queue_length_s = max_queue_length_e = max_queue_length_w = 0

    # temporarily increase simulation speed
    old_multiplier = simulationSpeedMultiplier
    # Simulates 24 Hours in 1 second
    simulationSpeedMultiplier = traffic_light_logic.simulationSpeedMultiplier = 10.0  # set the high multiplier

    print(f"Running fast simulation for {duration} seconds with multiplier {simulationSpeedMultiplier}")
    await asyncio.sleep(duration)  # let simulation run quickly

    # restore original simulation speed
    simulationSpeedMultiplier = old_multiplier
    traffic_light_logic.simulationSpeedMultiplier = old_multiplier

    avg_wait_time_n = total_wait_time_n / wait_count_n if wait_count_n > 0 else 0
    avg_wait_time_s = total_wait_time_s / wait_count_s if wait_count_s > 0 else 0
    avg_wait_time_e = total_wait_time_e / wait_count_e if wait_count_e > 0 else 0
    avg_wait_time_w = total_wait_time_w / wait_count_w if wait_count_w > 0 else 0
    metrics = {
        "max_wait_time_n": max_wait_time_n, "max_wait_time_s": max_wait_time_s, "max_wait_time_e": max_wait_time_e, "max_wait_time_w": max_wait_time_w,
        "max_queue_length_n": max_queue_length_n, "max_queue_length_s": max_queue_length_s, "max_queue_length_e": max_queue_length_e, "max_queue_length_w": max_queue_length_w,
        "avg_wait_time_n": avg_wait_time_n, "avg_wait_time_s": avg_wait_time_s, "avg_wait_time_e": avg_wait_time_e, "avg_wait_time_w": avg_wait_time_w
    }
    print("Fast simulation metrics:", metrics)
    return metrics

# Expose endpoint to run fast simulation
@app.get("/simulate_fast")
async def simulate_fast_endpoint():
    # Run fast simulation for specified duration, return metrics
    metrics = await run_fast_simulation()
    #await stop_simulation()
    return metrics

# Resets the simulation
def reset_simulation():
    global simulationTime, lastUpdateTime, cars, spawnRates, traffic_light_logic
    simulationTime = 0
    lastUpdateTime = None
    cars = []
    asyncio.create_task(traffic_light_logic.run_traffic_loop())
    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())


@app.on_event("startup")
async def on_startup():
    global simulation_running
    simulation_running = True
    asyncio.create_task(traffic_light_logic.run_traffic_loop())
    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
