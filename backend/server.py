"""
Traffic Junction Simulation Server

This FastAPI server simulates a traffic junction, managing real-time traffic light control,
vehicle movement, and client communication. It supports both user-defined and adaptive 
traffic control, allowing for comparison and optimization.

Key Features:
- Traffic Control: Supports adaptive and manual signal timing, real-time updates, and right-turn management.
- Vehicle Management: Dynamically spawns vehicles, tracks movement, and manages queues.
- Simulation Control: Adjustable speed, time tracking, and performance monitoring with fast-mode simulation.
- Client Communication: WebSocket-based live updates, REST API for settings, and CORS support.
- Data Collection: Tracks vehicle counts, wait times, and performance metrics for strategy evaluation.

The server provides a real-time visualization mode for interactive testing and a fast simulation mode 
for quick strategy comparison. Configuration options include lane count, spawn rates, traffic timing, 
and simulation speed. Connects to a frontend on port 8000.
"""

import sys
import os

# Add root project directory and backend folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))


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
from junction_objects.adaptive_controller import run_adaptive_traffic_loop

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Initialise FastAPI application
app = FastAPI()

# SQLite database connection string
db_path = "sqlite:///traffic_junction.db"

"""
Configuration for FastAPI application middleware and static file serving
"""

# Enable CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get base directory path for static file serving
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set static files directory path
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount static files directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# List to store WebSocket connections
connected_clients = []

# Initialise traffic light controller
traffic_light_logic = TrafficLightController()

# Simulation speed multiplier (1.0 = real time)
simulationSpeedMultiplier = 1.0  

# Store junction configuration data
junction_data = None

# Track simulation time
simulationTime = 0

# Track last update time for time calculations
lastUpdateTime = None

# Flag to control simulation running state
simulation_running = True

# Metrics tracking variables for each direction (North, South, East, West)
# Maximum wait times
max_wait_time_n = max_wait_time_s = max_wait_time_e = max_wait_time_w = 0

# Total wait times
total_wait_time_n = total_wait_time_s = total_wait_time_e = total_wait_time_w = 0

# Number of vehicles that have waited
wait_count_n = wait_count_s = wait_count_e = wait_count_w = 0

# Maximum queue lengths
max_queue_length_n = max_queue_length_s = max_queue_length_e = max_queue_length_w = 0

# Store vehicle spawn rate settings
spawnRates: Dict[str, Any] = {}

# Store junction configuration settings
junctionSettings: Dict[str, Any] = {}

# Store traffic light timing settings
trafficLightSettings: Dict[str, Any] = {}

# List to store active vehicles
cars = []

# Task reference for default traffic control loop
default_traffic_loop_task = None

async def broadcast_to_all(data_str: str):
    """
    Broadcasts a message to all connected WebSocket clients.
    Handles client disconnections gracefully by catching exceptions.
    
    Parameters:
        data_str (str): JSON string data to broadcast
    """
    for ws in connected_clients:
        try:
            await ws.send_text(data_str)
        except:
            pass

# Set broadcast callback for traffic light controller
traffic_light_logic.set_broadcast_callback(broadcast_to_all)

@app.post("/stop_simulation")
async def stop_simulation():
    """
    An endpoint that is used after ending a simulation and retrieving results,
    which is used to cleanly close out the simulation by clearing caches and closing
    client connections.
    
    Returns:
        JSONResponse with:
        - 400 status if no simulation is running
        - 200 status on successful stop
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
    Updates the simulation time by converting real-time seconds into simulated minutes.
    
    For every real-time second, the simulation advances by 1 simulated minute.
    This means that when simulationSpeedMultiplier = 1.0:
    - 1 second real time = 1 minute simulation time
    - 1 hour simulation time = 60 seconds real time
    
    The simulation time is broadcast to all connected clients to display the current
    simulated hours and minutes.
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
    Predefined Canvas Html data, which is used in front end,
    needed here for scaling.
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
    WebSocket endpoint for real-time vehicle and traffic simulation data streaming.
    
    Handles bi-directional communication between the traffic junction frontend and backend:
    - Accepts WebSocket connections from simulation frontend clients
    - Maintains list of connected clients for broadcasting vehicle positions and traffic states
    - Processes incoming canvas resizing messages to update junction dimensions
    - Handles simulation speed updates from frontend speed controls
    - Broadcasts periodic updates of vehicle positions, traffic light states and queues
    
    Flow:
    1. Accept client WebSocket connection
    2. Add client to broadcast list for vehicle/traffic updates
    3. Send initial traffic light configuration
    4. Process incoming messages:
        - Canvas sizing to properly place vehicles and junction elements
        - Speed multiplier updates to control simulation rate
    5. Remove client on disconnect
    
    Parameters:
        ws (WebSocket): WebSocket connection for streaming vehicle data
        
    Global state:
        junction_data: Current junction configuration and dimensions
        simulationSpeedMultiplier: Controls simulation update rate
        connected_clients: Active WebSocket connections for broadcasting
        
    Error handling:
        - JSON parsing for malformed messages
        - Connection cleanup on client disconnect
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
    Updates vehicle spawn rate settings based on client request.
    
    Accepts POST request with dictionary containing spawn rates for each direction and turn type.
    Updates global spawnRates and propagates changes to traffic light controller.
    
    Parameters:
        data: Dictionary containing spawn rates (vehicles per minute) for each 
                direction (N,S,E,W) and turn type (left,forward,right)
    """
    
    global spawnRates
    
    spawnRates = data
    
    traffic_light_logic.update_vehicle_data(spawnRates)
    
    print("Spawn rates updated:", spawnRates)
    
    return {"message": "Spawn rates updated successfully"}

@app.get("/spawn_rates")
def get_spawn_rates():
    """
    Retrieves current vehicle spawn rate settings.
    
    Returns the global spawnRates dictionary containing the current spawn rates 
    if available, otherwise returns message indicating no rates exist yet.
    
    Returns:
        Either current spawn rates or message if none exist
    """
    
    return spawnRates if spawnRates else {"message": "No spawn rates available yet"}

@app.post("/update_junction_settings")
def update_junction_settings(data: Dict[str, Any]):
    """
    Updates junction configuration settings based on client request.
    
    Accepts POST request with dictionary containing junction parameters.
    Updates global junctionSettings and propagates changes to traffic light controller.
    
    Parameters:
        data: Dictionary containing junction configuration parameters 
             like number of lanes, road dimensions, etc.
    """
    
    global junctionSettings
    
    junctionSettings = data
    
    traffic_light_logic.update_junction_settings(junctionSettings)
    
    print("Junction settings updated:", junctionSettings)
    
    return {"message": "Junction settings updated successfully"}

@app.get("/junction_settings") 
def get_junction_settings():
    """
    Retrieves current junction configuration settings.
    
    Returns the global junctionSettings dictionary containing the current
    junction configuration if available, otherwise returns message indicating
    no settings exist yet.
    
    Returns:
        Either current junction settings or message if none exist
    """
    
    return junctionSettings if junctionSettings else {"message": "No junction settings available yet"}

@app.post("/update_traffic_light_settings")
def update_traffic_light_settings(data: Dict[str, Any]):
    """
    Updates traffic light settings based on clients chosen configuration.
    Either enabled or disabled, confirming whether they want to compete with default algorithm
    
    Accepts POST request with dictionary containing traffic light timing parameters.
    Updates global trafficLightSettings and propagates changes to traffic light controller.
    
    Parameters:
        data: Dictionary containing traffic light configuration parameters
             like timing intervals, enabled states, etc.
    """
    
    global trafficLightSettings
    
    trafficLightSettings = data
    
    traffic_light_logic.update_traffic_settings(trafficLightSettings)
    
    print("Traffic light settings updated:", trafficLightSettings)
    
    return {"message": "Traffic light settings updated successfully"}

@app.get("/traffic_light_settings")
def get_traffic_light_settings():
    """
    Retrieves current traffic light settings.
    
    Returns the global trafficLightSettings dictionary containing the current
    traffic light configuration if available, otherwise returns message indicating
    no settings exist yet.
    
    Returns:
        Either current traffic light settings or message if none exist
    """
    
    return trafficLightSettings if trafficLightSettings else {"message": "No traffic light settings available yet"}

cars = []

def getLaneCandidates(numOfLanes):
    """
    Left Turns occur in left most lane alwways,
    Right Turns occur in right most lane always,
    and Forward Turns occur in middle lanes if they exist,
    or 1st lane in 1 or 2 lane config, else middle lanes
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
    Main loop for spawning vehicles in the simulation based on user-defined spawn rates.
    
    Key aspects:
    - Runs continuously while simulation is active
    - Spawns cars according to user-configured vehicles per minute (VPM) rates
    - Adjusts spawn rates based on simulation speed multiplier, 
      so that when the simulation speed increases so does spawning, 
      such that it maintains same behaviour across all simulation speeds.
    - Handles lane assignment for different turn types (left, forward, right)
    """
    
    global simulation_running, cars, junction_data
    
    # Wait for junction configuration to be available
    while junction_data is None:
        await asyncio.sleep(0.1)

    # Get lane configuration based on user-defined number of lanes
    numOfLanes = junction_data["numOfLanes"]
    leftLane, rightLane, forwardLanes = getLaneCandidates(numOfLanes)

    while simulation_running:
        
        if not simulation_running:
            print("Stopping car-spawning loop.")
            break

        # Process each direction (NESW) defined in the user's junction settings
        for direction in ["north", "east", "south", "west"]:
            
            # Process each turn type based on user's spawn rate settings
            for turnType in ["left", "forward", "right"]:
                
                # Get base spawn rate (vehicles per minute) from user settings
                base_vpm = spawnRates[direction][turnType]
                # Adjust spawn rate based on simulation speed multiplier
                effective_vpm = base_vpm * simulationSpeedMultiplier
                
                # Skip if spawn rate is zero
                if effective_vpm <= 0:
                    continue
                
                # Convert VPM to probability per frame
                # e.g., 60 VPM = 1 car/sec = ~0.017 probability per frame at normal speed
                prob = effective_vpm / 60.0
                
                # Randomly determine if car should spawn this frame
                if random.random() < prob:
                    
                    # Assign lane based on turn type
                    if turnType == "left":
                        lane = leftLane  # Always use leftmost lane for left turns
                        
                    elif turnType == "right":
                        lane = rightLane  # Always use rightmost lane for right turns
                        
                    else:  # Forward movement
                        if forwardLanes:
                            # Rotate through available forward lanes to distribute traffic
                            idx = forwardIndex[direction] % len(forwardLanes)
                            lane = forwardLanes[idx]
                            forwardIndex[direction] += 1
                        else:
                            lane = 0  # Default to lane 0 if no forward lanes available

                    # Base speed in pixels per frame
                    speed = 4.0
                    
                    # Create new vehicle with user/junction settings
                    new_car = Car(
                        direction=direction,
                        lane=lane,
                        speed=speed,
                        turn_type=turnType,
                        junctionData=junction_data
                    )
                    
                    # Initialise tracking variables for wait time metrics
                    new_car.spawn_time = simulationTime
                    new_car.wait_recorded = False
                    
                    # Add to global car list
                    cars.append(new_car)

        # Control spawn loop rate based on simulation speed
        # Higher speed = faster checking for spawns
        await asyncio.sleep(1 / simulationSpeedMultiplier)

def isOffCanvas(car):
    """
    Once the car has completed its movemement and driven off the canvas,
    we return true, so they can be removed from the Cars array.
    So it speeds up searches and retrievals concering cars.
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
    Main loop for updating all vehicles in the simulation. Handles:
    - Vehicle movement and position updates
    - Traffic light interaction
    - Wait time tracking
    - Queue length monitoring
    - Broadcasting vehicle positions to clients

    Wait Time is continuously tracked, and so is queue length, 
    right up until the car crosses the stop line, and thus has entered the junction.
    """
    
    global cars, junction_data, simulation_running

    # Wait until junction data is available before starting
    while junction_data is None:
        await asyncio.sleep(0.1)

    while simulation_running:
        if not simulation_running:
            print("Stopping car-update loop.")
            break

        # Get current traffic light states
        main_lights = traffic_light_logic.trafficLightStates
        right_lights = traffic_light_logic.rightTurnLightStates

        # Update each car's position and speed
        for c in cars:
            base_speed = 4.0  # Base speed in pixels per frame
            c.speed = base_speed * simulationSpeedMultiplier
            update_vehicle(c, main_lights, right_lights, cars)

        # Remove cars that have left the canvas
        cars[:] = [car for car in cars if not isOffCanvas(car)]

        # Access global variables for tracking metrics
        global max_wait_time_n, max_wait_time_s, max_wait_time_e, max_wait_time_w
        global total_wait_time_n, total_wait_time_s, total_wait_time_e, total_wait_time_w
        global wait_count_n, wait_count_s, wait_count_e, wait_count_w
        global max_queue_length_n, max_queue_length_s, max_queue_length_e, max_queue_length_w

        # Initialise counters for current queue lengths
        north_waiting_count = south_waiting_count = east_waiting_count = west_waiting_count = 0

        # Process each car to update wait times and queue lengths
        for c in cars:
            # Initialise tracking attributes if they don't exist
            if not hasattr(c, 'spawn_time'):
                c.spawn_time = simulationTime
            if not hasattr(c, 'wait_recorded'):
                c.wait_recorded = False
            if not hasattr(c, 'prev_wait_time'):
                c.prev_wait_time = 0

            # Handle north-bound traffic
            if c.inital_direction == "north":
                if not c.wait_recorded:
                    wait_count_n += 1  # Increment total vehicles that have waited
                    c.wait_recorded = True
                if not has_crossed_line(c):  # If car hasn't crossed stop line
                    wait_time = simulationTime - c.spawn_time
                    max_wait_time_n = max(max_wait_time_n, wait_time)
                    # Update total wait time by removing previous and adding new
                    total_wait_time_n -= c.prev_wait_time
                    total_wait_time_n += wait_time
                    north_waiting_count += 1
                c.prev_wait_time = wait_time

            # Similar logic for south-bound traffic
            elif c.inital_direction == "south":
                if not c.wait_recorded:
                    wait_count_s += 1
                    c.wait_recorded = True
                if not has_crossed_line(c):
                    wait_time = simulationTime - c.spawn_time
                    max_wait_time_s = max(max_wait_time_s, wait_time)
                    total_wait_time_s -= c.prev_wait_time
                    total_wait_time_s += wait_time
                    south_waiting_count += 1
                c.prev_wait_time = wait_time

            # Similar logic for east-bound traffic
            elif c.inital_direction == "east":
                if not c.wait_recorded:
                    wait_count_e += 1
                    c.wait_recorded = True
                if not has_crossed_line(c):
                    wait_time = simulationTime - c.spawn_time
                    max_wait_time_e = max(max_wait_time_e, wait_time)
                    total_wait_time_e -= c.prev_wait_time
                    total_wait_time_e += wait_time
                    east_waiting_count += 1
                c.prev_wait_time = wait_time

            # Similar logic for west-bound traffic
            elif c.inital_direction == "west":
                if not c.wait_recorded:
                    wait_count_w += 1
                    c.wait_recorded = True
                if not has_crossed_line(c):
                    wait_time = simulationTime - c.spawn_time
                    max_wait_time_w = max(max_wait_time_w, wait_time)
                    total_wait_time_w -= c.prev_wait_time
                    total_wait_time_w += wait_time
                    west_waiting_count += 1
                c.prev_wait_time = wait_time

        # Update maximum queue lengths for each direction
        max_queue_length_n = max(max_queue_length_n, north_waiting_count)
        max_queue_length_s = max(max_queue_length_s, south_waiting_count)
        max_queue_length_e = max(max_queue_length_e, east_waiting_count)
        max_queue_length_w = max(max_queue_length_w, west_waiting_count)

        # Broadcast updated car positions to all connected clients
        data = {"cars": [car.to_dict() for car in cars]}
        await broadcast_to_all(json.dumps(data))

        if not simulation_running:
            break
            
        # Control update rate based on simulation speed
        await asyncio.sleep((1 / 60) / simulationSpeedMultiplier)

async def run_fast_simulation():
    """
    Runs two separate traffic simulations in sequence to compare user-defined and default traffic control settings.
    This function executes two 5-second simulations at 10x speed, equating to 50 mins of Simulation Time:
    1. First run uses user-defined traffic light settings
    2. Second run uses adaptive/default traffic control algorithm

    The function tracks and compares key metrics for both simulations including:
    - Maximum wait times for vehicles in each direction (N,S,E,W)
    - Average wait times for vehicles in each direction
    - Maximum queue lengths in each direction

    Global variables used:
    - simulationSpeedMultiplier: Controls simulation speed
    - simulationTime: Tracks elapsed simulation time
    - max_wait_time_[n,s,e,w]: Tracks longest wait per direction
    - total_wait_time_[n,s,e,w]: Tracks cumulative wait times
    - wait_count_[n,s,e,w]: Counts number of waiting vehicles
    - max_queue_length_[n,s,e,w]: Tracks longest queues
    - default_traffic_loop_task: Background task for traffic control

    Returns:
        dict: Contains two nested dictionaries 'user' and 'default' with simulation results.
              Each nested dict contains max_wait_times, max_queue_lengths, and avg_wait_times
              for all directions.
    Note:
        Simulation speed is temporarily increased to 10x during runs and restored afterwards.
        All metrics are reset between runs for accurate comparison.
    """

    global simulationSpeedMultiplier, simulationTime
    global max_wait_time_n, max_wait_time_s, max_wait_time_e, max_wait_time_w
    global total_wait_time_n, total_wait_time_s, total_wait_time_e, total_wait_time_w
    global wait_count_n, wait_count_s, wait_count_e, wait_count_w
    global max_queue_length_n, max_queue_length_s, max_queue_length_e, max_queue_length_w
    global default_traffic_loop_task

    duration = 5.0

    old_multiplier = simulationSpeedMultiplier
    simulationSpeedMultiplier = traffic_light_logic.simulationSpeedMultiplier = 10.0

    # First Run is for user traffic settings

    reset_simulation()

    max_wait_time_n = max_wait_time_s = max_wait_time_e = max_wait_time_w = 0
    total_wait_time_n = total_wait_time_s = total_wait_time_e = total_wait_time_w = 0
    wait_count_n = wait_count_s = wait_count_e = wait_count_w = 0
    max_queue_length_n = max_queue_length_s = max_queue_length_e = max_queue_length_w = 0

    await asyncio.sleep(duration)

    user_avg_wait_time_n = total_wait_time_n / wait_count_n if wait_count_n > 0 else total_wait_time_n
    user_avg_wait_time_s = total_wait_time_s / wait_count_s if wait_count_s > 0 else total_wait_time_s
    user_avg_wait_time_e = total_wait_time_e / wait_count_e if wait_count_e > 0 else total_wait_time_e
    user_avg_wait_time_w = total_wait_time_w / wait_count_w if wait_count_w > 0 else total_wait_time_w

    user_results = {
        "max_wait_time_n": max_wait_time_n, 
        "max_wait_time_s": max_wait_time_s, 
        "max_wait_time_e": max_wait_time_e, 
        "max_wait_time_w": max_wait_time_w,
        "max_queue_length_n": max_queue_length_n, 
        "max_queue_length_s": max_queue_length_s, 
        "max_queue_length_e": max_queue_length_e, 
        "max_queue_length_w": max_queue_length_w,
        "avg_wait_time_n": user_avg_wait_time_n, 
        "avg_wait_time_s": user_avg_wait_time_s, 
        "avg_wait_time_e": user_avg_wait_time_e, 
        "avg_wait_time_w": user_avg_wait_time_w
    }

    # Run the algo traffic settings after user

    default_traffic_loop_task.cancel()

    try:
        await default_traffic_loop_task
    except asyncio.CancelledError:
        print("Default traffic loop cancelled.")

    reset_simulation()
    asyncio.create_task(run_adaptive_traffic_loop(traffic_light_logic, cars, 0.0005))

    max_wait_time_n = max_wait_time_s = max_wait_time_e = max_wait_time_w = 0
    total_wait_time_n = total_wait_time_s = total_wait_time_e = total_wait_time_w = 0
    wait_count_n = wait_count_s = wait_count_e = wait_count_w = 0
    max_queue_length_n = max_queue_length_s = max_queue_length_e = max_queue_length_w = 0

    await asyncio.sleep(duration)

    def_avg_wait_time_n = total_wait_time_n / wait_count_n if wait_count_n > 0 else total_wait_time_n
    def_avg_wait_time_s = total_wait_time_s / wait_count_s if wait_count_s > 0 else total_wait_time_s
    def_avg_wait_time_e = total_wait_time_e / wait_count_e if wait_count_e > 0 else total_wait_time_e
    def_avg_wait_time_w = total_wait_time_w / wait_count_w if wait_count_w > 0 else total_wait_time_w

    default_results = {
        "max_wait_time_n": max_wait_time_n, 
        "max_wait_time_s": max_wait_time_s, 
        "max_wait_time_e": max_wait_time_e, 
        "max_wait_time_w": max_wait_time_w,
        "max_queue_length_n": max_queue_length_n, 
        "max_queue_length_s": max_queue_length_s, 
        "max_queue_length_e": max_queue_length_e, 
        "max_queue_length_w": max_queue_length_w,
        "avg_wait_time_n": def_avg_wait_time_n, 
        "avg_wait_time_s": def_avg_wait_time_s, 
        "avg_wait_time_e": def_avg_wait_time_e, 
        "avg_wait_time_w": def_avg_wait_time_w
    }

    print("[RUN #2] Complete. Default logic results:", default_results)

    simulationSpeedMultiplier = old_multiplier
    traffic_light_logic.simulationSpeedMultiplier = old_multiplier

    return {
        "user": user_results,
        "default": default_results,
    }

@app.get("/simulate_fast")
async def simulate_fast_endpoint():
    """
    Endpoint to run a fast simulation running user settings first if enabled 
    then running default adaptive settings, comparing user and adaptive traffic light timings.
    
    Calls run_fast_simulation() to run two simulation scenarios with higher speed:
    1. User-configured traffic light timings
    2. Adaptive traffic light algorithm
    
    Returns:
        dict: Performance metrics for both scenarios including:
        - Maximum wait times for each direction
        - Maximum queue lengths for each direction
        - Average wait times for each direction
    """
    
    metrics = await run_fast_simulation()
    
    return metrics

def reset_simulation():
    """
    Resets the simulation state by:
    - Resetting simulation time to 0
    - Clearing lastUpdateTime
    - Emptying cars list
    - Restarting core simulation loops for:
      - Vehicle spawning
      - Vehicle updates 
      - Time updates

    Used before running the simulation fast in the backend.
    """

    global simulationTime, lastUpdateTime, cars, spawnRates, traffic_light_logic
    simulationTime = 0
    lastUpdateTime = None
    cars = []

    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())

@app.on_event("startup")
async def on_startup():
    """
    Initialise simulation tasks when the FastAPI server starts up.
    Sets simulation_running to True and starts the following async tasks:
    - Traffic light control loop (either standard or adaptive based on client settings)
    - Client choses to see our default dynamic simulation or their own traffic light simulation.
    - Vehicle spawning loop
    - Vehicle update loop 
    - Simulation time update loop
    """
    
    global simulation_running, default_traffic_loop_task
    simulation_running = True

    default_traffic_loop_task = asyncio.create_task(run_traffic_loop_wrapper())

    # Start core simulation loops
    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())

async def run_traffic_loop_wrapper():
    # Wait until the clients chosen traffic settings are either enabled or disabled
    while not trafficLightSettings:
        await asyncio.sleep(0.1)  
    
    # Once users chosen settings are available, start the proper traffic loop
    if trafficLightSettings.get("traffic-light-enable", False):
        print("using user")
        await run_traffic_loop(traffic_light_logic)
    else:
        print("using algo")
        await run_adaptive_traffic_loop(traffic_light_logic, cars, 1.0)


if __name__ == "__main__":
    # Start the FastAPI server on host 0.0.0.0 (all available network interfaces) and port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)