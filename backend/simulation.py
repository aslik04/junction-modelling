# backend/simulation.py

"""

"""

import asyncio
import json
import random
from typing import Any, Dict

from fastapi import WebSocket

# Relative import from the "junction_objects" subfolder
from .junction_objects.traffic_light_state import run_traffic_loop
from .junction_objects.traffic_light_controller import TrafficLightController
from .junction_objects.vehicle import Car
from .junction_objects.vehicle_movement import update_vehicle
from .junction_objects.vehicle_stop_line import has_crossed_line

from .globals import (
    simulation_running,
    simulationSpeedMultiplier,
    simulationTime,
    lastUpdateTime,
    connected_clients,
    cars,
    spawnRates,
    junctionSettings,
    trafficLightSettings,
    max_wait_time_n,
    max_wait_time_s,
    max_wait_time_e,
    max_wait_time_w,
    total_wait_time_n,
    total_wait_time_s,
    total_wait_time_e,
    total_wait_time_w,
    wait_count_n,
    wait_count_s,
    wait_count_e,
    wait_count_w,
    max_queue_length_n,
    max_queue_length_s,
    max_queue_length_e,
    max_queue_length_w,
    junction_data,
)

traffic_light_logic = TrafficLightController()

backend_results = False

forwardIndex = {
    "north": 0,
    "east":  0,
    "south": 0,
    "west":  0
}


async def on_startup_event(app):
    """

    """
    global simulation_running
    simulation_running = True

    traffic_light_logic.set_broadcast_callback(broadcast_to_all)

    asyncio.create_task(run_traffic_loop(traffic_light_logic))
    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())


async def broadcast_to_all(data_str: str):
    """

    """
    for ws in connected_clients:
        try:
            await ws.send_text(data_str)
        except:
            pass


async def update_simulation_time():
    """

    """
    global simulation_running, simulationTime, lastUpdateTime, simulationSpeedMultiplier

    loop = asyncio.get_event_loop()
    while simulation_running:
        now = loop.time()
        if lastUpdateTime is None:
            lastUpdateTime = now

        delta = now - lastUpdateTime
        lastUpdateTime = now

        simulationTime += delta * simulationSpeedMultiplier * 60

        simulatedHours = int(simulationTime // 3600)
        simulatedMinutes = int((simulationTime % 3600) // 60)
        time_str = f"{simulatedHours}h {simulatedMinutes}m"

        await broadcast_to_all(json.dumps({"simulatedTime": time_str}))
        await asyncio.sleep(1 / 60)


def create_junction_data(canvas_width, canvas_height, num_of_lanes, pixelWidthOfLane=20) -> dict:
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


async def spawn_car_loop():
    """

    """
    global simulation_running, cars, junction_data

    while junction_data is None:
        await asyncio.sleep(0.1)

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

    numOfLanes = junction_data["numOfLanes"]
    leftLane, rightLane, forwardLanes = getLaneCandidates(numOfLanes)

    while simulation_running:
        if not simulation_running:
            print("Stopping spawn loop.")
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


async def update_car_loop():
    """

    """
    global cars, junction_data, simulation_running
    global max_wait_time_n, max_wait_time_s, max_wait_time_e, max_wait_time_w
    global total_wait_time_n, total_wait_time_s, total_wait_time_e, total_wait_time_w
    global wait_count_n, wait_count_s, wait_count_e, wait_count_w
    global max_queue_length_n, max_queue_length_s, max_queue_length_e, max_queue_length_w
    global simulationTime, simulationSpeedMultiplier

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

        # remove off-canvas
        cars[:] = [car for car in cars if not isOffCanvas(car)]

        north_waiting_count = south_waiting_count = east_waiting_count = west_waiting_count = 0

        for c in cars:
            if not hasattr(c, "spawn_time"):
                c.spawn_time = simulationTime
            if not hasattr(c, "wait_recorded"):
                c.wait_recorded = False

            # crossing stop line logic
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

        max_queue_length_n = max(max_queue_length_n, north_waiting_count)
        max_queue_length_s = max(max_queue_length_s, south_waiting_count)
        max_queue_length_e = max(max_queue_length_e, east_waiting_count)
        max_queue_length_w = max(max_queue_length_w, west_waiting_count)

        data = {"cars": [car.to_dict() for car in cars]}
        await broadcast_to_all(json.dumps(data))
        await asyncio.sleep((1 / 60) / simulationSpeedMultiplier)


def isOffCanvas(car: Car) -> bool:
    """

    """
    jd = car.junctionData
    cw = jd["canvasWidth"]
    ch = jd["canvasHeight"]
    h  = car.height

    if car.inital_direction == "north":
        if car.turn_type == "forward" and car.y < -h:
            return True
        elif car.turn_type == "left" and car.x < -h:
            return True
        elif car.turn_type == "right" and car.x > cw + h:
            return True

    elif car.inital_direction == "south":
        if car.turn_type == "forward" and car.y > ch + h:
            return True
        elif car.turn_type == "left" and car.x > cw + h:
            return True
        elif car.turn_type == "right" and car.x < -h:
            return True

    elif car.inital_direction == "east":
        if car.turn_type == "forward" and car.x > cw + h:
            return True
        elif car.turn_type == "left" and car.y < -h:
            return True
        elif car.turn_type == "right" and car.y > ch + h:
            return True

    elif car.inital_direction == "west":
        if car.turn_type == "forward" and car.x < -h:
            return True
        elif car.turn_type == "left" and car.y > ch + h:
            return True
        elif car.turn_type == "right" and car.y < -h:
            return True

    return False


async def run_fast_simulation() -> dict:
    """
    """
    global backend_results
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
    wait_count_n = wait_count_s = wait_count_e = 0
    max_queue_length_n = max_queue_length_s = max_queue_length_e = max_queue_length_w = 0

    old_multiplier = simulationSpeedMultiplier
    simulationSpeedMultiplier = traffic_light_logic.simulationSpeedMultiplier = 10.0

    print(f"Running fast simulation for {duration}s at multiplier {simulationSpeedMultiplier} ...")
    await asyncio.sleep(duration)

    simulationSpeedMultiplier = old_multiplier
    traffic_light_logic.simulationSpeedMultiplier = old_multiplier

    def safe_avg(total, count):
        return total / count if count > 0 else 0

    avg_wait_time_n = safe_avg(total_wait_time_n, wait_count_n)
    avg_wait_time_s = safe_avg(total_wait_time_s, wait_count_s)
    avg_wait_time_e = safe_avg(total_wait_time_e, wait_count_e)
    avg_wait_time_w = safe_avg(total_wait_time_w, wait_count_w)

    backend_results = False

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

def reset_simulation():
    """

    """
    global simulationTime, lastUpdateTime, cars
    simulationTime = 0
    lastUpdateTime = None
    cars.clear()

    asyncio.create_task(run_traffic_loop(traffic_light_logic))
    asyncio.create_task(spawn_car_loop())
    asyncio.create_task(update_car_loop())
    asyncio.create_task(update_simulation_time())