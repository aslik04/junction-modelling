"""

"""

import asyncio
import random

def get_vertical_wait_count(cars: list) -> int:
    return sum(1 for car in cars if car.inital_direction in ("north", "south") and not car.passedStopLine and car.turn_type != "right")

def get_horizontal_wait_count(cars: list) -> int:
    return sum(1 for car in cars if car.inital_direction in ("east", "west") and not car.passedStopLine and car.turn_type != "right")

def get_vertical_right_wait_count(cars: list) -> int:
    return sum(1 for car in cars if car.inital_direction in ("north", "south") and car.turn_type == "right" and not car.passedStopLine)

def get_horizontal_right_wait_count(cars: list) -> int:
    return sum(1 for car in cars if car.inital_direction in ("east", "west") and car.turn_type == "right" and not car.passedStopLine)

def nonlinear_green(count: int, min_green: float, max_green: float, k: float = 2.0) -> float:
    return min_green + (max_green - min_green) * (count / (count + k))

async def set_phase(controller, phase: str) -> None:
    if phase == "vertical":
        controller.trafficLightStates["north"] = {"red": False, "amber": False, "green": True}
        controller.trafficLightStates["south"] = {"red": False, "amber": False, "green": True}
        controller.trafficLightStates["east"] = {"red": True, "amber": False, "green": False}
        controller.trafficLightStates["west"] = {"red": True, "amber": False, "green": False}
    elif phase == "horizontal":
        controller.trafficLightStates["east"] = {"red": False, "amber": False, "green": True}
        controller.trafficLightStates["west"] = {"red": False, "amber": False, "green": True}
        controller.trafficLightStates["north"] = {"red": True, "amber": False, "green": False}
        controller.trafficLightStates["south"] = {"red": True, "amber": False, "green": False}
    elif phase == "red":
        for d in ["north", "east", "south", "west"]:
            controller.trafficLightStates[d] = {"red": True, "amber": False, "green": False}
    await controller._broadcast_state()

async def run_right_turn_phase(controller, directions: list, phase_time: float, sim_speed: float, transition_time: float) -> None:
    for d in directions:
        controller.rightTurnLightStates[d] = {"off": False, "on": True}
    await controller._broadcast_state()
    await asyncio.sleep(phase_time / sim_speed)
    for d in directions:
        controller.rightTurnLightStates[d] = {"off": True, "on": False}
    await controller._broadcast_state()
    await asyncio.sleep(transition_time / sim_speed)

async def run_pedestrian_event(controller) -> None:
    for d in ["north", "east", "south", "west"]:
        controller.trafficLightStates[d] = {"red": True, "amber": False, "green": False}
        controller.rightTurnLightStates[d] = {"off": True, "on": False}
        await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)
        controller.pedestrianLightStates[d] = {"off": False, "on": True}
    await controller._broadcast_state()
    await asyncio.sleep(controller.pedestrianDuration / controller.simulationSpeedMultiplier)
    for d in ["north", "east", "south", "west"]:
        controller.pedestrianLightStates[d] = {"off": True, "on": False}
    await controller._broadcast_state()

async def run_adaptive_traffic_loop(controller, cars: list, gap: float = 0.005) -> None:
    min_green = 2
    max_green = 20
    k = 2.0
    transition_time = gap_time = gap
    right_turn_duration = 3.0
    smoothing_alpha = 0.0
    smoothed_vertical = min_green
    smoothed_horizontal = min_green
    loop = asyncio.get_event_loop()
    minute_start = loop.time()
    events_this_minute = 0
    gaps_this_minute = 0
    while True:
        sim_speed = controller.simulationSpeedMultiplier
        vertical_count = get_vertical_wait_count(cars)
        horizontal_count = get_horizontal_wait_count(cars)
        vertical_right_count = get_vertical_right_wait_count(cars)
        horizontal_right_count = get_horizontal_right_wait_count(cars)
        desired_vertical = nonlinear_green(vertical_count, min_green, max_green, k) if vertical_count > 0 else 0
        desired_horizontal = nonlinear_green(horizontal_count, min_green, max_green, k) if horizontal_count > 0 else 0
        smoothed_vertical = (1 - smoothing_alpha) * smoothed_vertical + smoothing_alpha * desired_vertical
        smoothed_horizontal = (1 - smoothing_alpha) * smoothed_horizontal + smoothing_alpha * desired_horizontal
        now = loop.time()
        if now - minute_start >= 60:
            minute_start = now
            events_this_minute = 0
            gaps_this_minute = 0
        if smoothed_vertical > 0:
            await set_phase(controller, "vertical")
            await asyncio.sleep(smoothed_vertical / sim_speed)
            await set_phase(controller, "red")
            await asyncio.sleep(transition_time / sim_speed)
        else:
            await set_phase(controller, "red")
            await asyncio.sleep(gap_time / sim_speed)
        if vertical_right_count > 0:
            await run_right_turn_phase(controller, ["north", "south"], right_turn_duration, sim_speed, transition_time)
        else:
            await asyncio.sleep(gap_time / sim_speed)
        if smoothed_horizontal > 0:
            await set_phase(controller, "horizontal")
            await asyncio.sleep(smoothed_horizontal / sim_speed)
            await set_phase(controller, "red")
            await asyncio.sleep(transition_time / sim_speed)
        else:
            await set_phase(controller, "red")
            await asyncio.sleep(gap_time / sim_speed)
        if horizontal_right_count > 0:
            await run_right_turn_phase(controller, ["east", "west"], right_turn_duration, sim_speed, transition_time)
        else:
            await asyncio.sleep(gap_time / sim_speed)
        gaps_this_minute += 2
        now = loop.time()
        if now - minute_start >= 60:
            minute_start = now
            events_this_minute = 0
            gaps_this_minute = 0
        remaining_gaps = (2 * 60) - gaps_this_minute
        remaining_events = controller.pedestrianPerMinute - events_this_minute
        p_gap = (remaining_events / remaining_gaps) if remaining_gaps > 0 else 0
        if random.random() < p_gap:
            await run_pedestrian_event(controller)
            events_this_minute += 1
        await asyncio.sleep(gap_time / sim_speed)