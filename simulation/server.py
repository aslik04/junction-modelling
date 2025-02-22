import asyncio
import json
import random
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from trafficLights import TrafficLightLogic
from car_logic import Car

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="../static"), name="static")

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
spawnRates = {
    "north": {"forward": 200,  "left": 180, "right": 150},
    "east":  {"forward": 200, "left": 150,  "right": 180},
    "south": {"forward": 105, "left": 170,  "right": 140},
    "west":  {"forward": 205, "left": 100, "right": 130}
}

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
        data = {"cars": [c.to_dict() for c in cars]}
        await broadcast_to_all(json.dumps(data))
        await asyncio.sleep((1/60) / simulationSpeedMultiplier)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(traffic_light_logic.run_traffic_loop())
    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
