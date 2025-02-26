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
import math

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

# Per-direction metrics
directions = ["north", "east", "south", "west"]
metrics = {
    d: {
        "max_wait_time": 0,      # maximum wait time for this direction (s)
        "total_wait_time": 0,    # total wait time for all cars in this direction
        "wait_count": 0,         # number of cars measured for this direction
        "max_queue_length": 0    # maximum queue length for this direction
    } for d in directions
}

@app.post("/stop_simulation")
async def stop_simulation():
    """
    Stop the running simulation properly.
    """
    global simulation_running, connected_clients, cars

    if not simulation_running:
        return JSONResponse(status_code=400, content={"error": "No running simulation found"})
    #print("Stopping sim")
    simulation_running = False
    cars.clear()
    for ws in connected_clients:
        try:
            await ws.close()
        except:
            pass  # Ignore errors
    connected_clients.clear()
    #print("Simulation successfully stopped.")
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
                    #print(f"Received canvasSize: {width}x{height}, junction_data set: {junction_data}")
                elif data.get("type") == "speedUpdate":
                    new_speed = data["speed"]
                    simulationSpeedMultiplier = new_speed  # update global multiplier
                    traffic_light_logic.simulationSpeedMultiplier = new_speed  # update in traffic lights
                    #print("Updated simulation speed multiplier:", new_speed)
            except Exception as e:
                print("Error processing message:", e)
    except Exception as e:
        print("WebSocket error:", e)
    finally:
        if ws in connected_clients:
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
    #print("Spawn rates updated:", spawnRates)  # Debugging
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
    #print("Junction settings updated:", junctionSettings)
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
            #print("Stopping car spawning loop")
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
                    new_car = Car(direction, lane, speed=2.0, turn_type=turnType, jd=junction_data)
                    new_car.spawn_time = simulationTime  # simulation time when car spawns
                    new_car.wait_recorded = False        # ensure wait time recorded only once
                    cars.append(new_car)
                    #print(f"Spawned {direction} {turnType} car in lane {lane}")
        if not simulation_running: 
            break
        await asyncio.sleep(1)



def isOffCanvas(car):
    # Check based on the direction of travel
    if car.direction == "north":
        # Northbound cars leave at the top.
        if car.y < -200:
            return True
    elif car.direction == "south":
        # Southbound cars leave at the bottom.
        if car.y > (junction_data["canvasHeight"] + 200):
            return True
    elif car.direction == "east":
        # Eastbound cars leave on the right.
        if car.x > (junction_data["canvasWidth"] + 200):
            return True
    elif car.direction == "west":
        # Westbound cars leave on the left.
        if car.x < -200:
            return True
    return False


async def update_car_loop():
    global cars, junction_data, simulation_running, simulationTime, metrics, simulationSpeedMultiplier
    while simulation_running:
        if not simulation_running:
            #print("Stopping car update loop")
            break 
        main_lights = traffic_light_logic.trafficLightStates
        right_lights = traffic_light_logic.rightTurnLightStates

        # Update each car’s movement.
        for c in cars:
            base_speed = 2.0
            c.speed = base_speed * simulationSpeedMultiplier
            c.update(main_lights, right_lights, cars)
        # Remove cars that are off-canvas.
        cars = [c for c in cars if not isOffCanvas(c)]

        # Process each car: if it hasn't been processed, mark spawn and add to queue.
        for c in cars:
            if not hasattr(c, 'spawn_time'):
                c.spawn_time = simulationTime
                
            if not hasattr(c, 'wait_recorded'):
                c.wait_recorded = False
            if not hasattr(c, 'in_queue'):
                c.in_queue = True

            d = c.direction  # the car's direction
            stop_line = c.get_stop_line()  # the car's stop line value

            # If the car hasn't yet been recorded and it has passed its stop line, record its wait time.
            if not c.wait_recorded:
                if (d == "north" and c.y <= stop_line) or \
                   (d == "south" and c.y >= stop_line) or \
                   (d == "east"  and c.x >= stop_line) or \
                   (d == "west"  and c.x <= stop_line):
                    
                    # Increase the count of measured cars for this direction.
                    metrics[c.direction]["wait_count"] += 1
                    
                    # Calculate simulation wait time (in simulation seconds)
                    sim_wait_time = simulationTime - c.spawn_time
                    # Convert simulation seconds to raw seconds.
                    raw_wait_time = sim_wait_time / 60

                    metrics[d]["max_wait_time"] = max(metrics[d]["max_wait_time"], raw_wait_time)
                    metrics[d]["total_wait_time"] += raw_wait_time
                    c.wait_recorded = True
                    c.in_queue = False


        # Calculate current queue lengths per direction (cars still marked in_queue)
        current_queue_length = {
            d: sum(1 for c in cars if c.direction == d and c.in_queue)
            for d in directions
        }

        # Update the maximum queue length for each direction
        for d in directions:
            metrics[d]["max_queue_length"] = max(metrics[d]["max_queue_length"], current_queue_length[d])

        data = {
            "cars": [c.to_dict() for c in cars],
            "metrics": metrics  # optional: send metrics to clients
        }
        await broadcast_to_all(json.dumps(data))
        if not simulation_running:
            break
        await asyncio.sleep((1/60) / simulationSpeedMultiplier)


###############################################################################
# Used for fast simulation (calculating scores)
###############################################################################

async def run_fast_simulation():
    global simulationSpeedMultiplier, metrics

    duration = 1

    # Reset the simulation (this now restarts the simulation tasks)
    reset_fast_simulation()

    directions = ["north", "east", "south", "west"]
    metrics = {
        d: {
            "max_wait_time": 0,
            "total_wait_time": 0,
            "wait_count": 0,
            "max_queue_length": 0
        } for d in directions
    }

    # Temporarily increase simulation speed (10000 might be too high; consider lowering it)
    old_multiplier = simulationSpeedMultiplier
    simulationSpeedMultiplier = traffic_light_logic.simulationSpeedMultiplier = 10000.0

    #print(f"Running fast simulation for {duration} seconds with multiplier {simulationSpeedMultiplier}")
    await asyncio.sleep(duration)

    for d in directions:
        print(metrics[d]["max_wait_time"])

    simulationSpeedMultiplier = old_multiplier
    traffic_light_logic.simulationSpeedMultiplier = old_multiplier

    # Compute average wait time per direction.
    avg_wait_time = {}
    for d in metrics:
        if metrics[d]["wait_count"] > 0:
            avg_wait_time[d] = metrics[d]["total_wait_time"] / metrics[d]["wait_count"]
        else:
            avg_wait_time[d] = 0

    final_metrics = {
        "max_wait_time": { d: metrics[d]["max_wait_time"] for d in metrics },
        "max_queue_length": { d: metrics[d]["max_queue_length"] for d in metrics },
        "avg_wait_time": avg_wait_time,
    }
    print("Fast simulation metrics:", final_metrics)
    return final_metrics



# Expose endpoint to run fast simulation
@app.get("/simulate_fast")
async def simulate_fast_endpoint():
    # Run fast simulation for specified duration, return metrics
    metrics = await run_fast_simulation()
    print(metrics)
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

def reset_fast_simulation():
    global simulationTime, lastUpdateTime, cars, simulation_running, metrics
    metrics = {
        d: {"max_wait_time": 0, "total_wait_time": 0, "wait_count": 0, "max_queue_length": 0}
        for d in directions
    }
    simulationTime = 0
    lastUpdateTime = None
    cars = []
    simulation_running = True  # Restart simulation
    # Restart the tasks that update the simulation:
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
