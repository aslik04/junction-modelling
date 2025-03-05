import asyncio
import time
from typing import List
from junction_objects.traffic_light_controller import TrafficLightController
from junction_objects.enums import Direction, TrafficLightSignal
from junction_objects.vehicle_stop_line import has_crossed_line

# Global variables: track last serve times and simulation start time
last_serve_time = {
    "NS_MAIN": 0.0,
    "NS_RIGHT": 0.0,
    "EW_MAIN": 0.0,
    "EW_RIGHT": 0.0
}
start_time = time.time()

def get_time_since_start() -> float:
    """Return elapsed time since the simulation started."""
    return time.time() - start_time

def count_waiting_vehicles(cars: List, direction: str, turn_type: str, stop_threshold: float = 50.0) -> int:
    """
    Return the number of vehicles from 'cars' coming in 'direction' 
    with the given 'turn_type' that have not crossed the stop line.
    """
    return sum(
        1
        for c in cars
        if c.inital_direction == direction and c.turn_type == turn_type and not has_crossed_line(c)
    )

def get_total_queue(cars: List, direction: str, include_left_forward: bool = True, include_right: bool = True) -> int:
    """
    Returns the total number of waiting vehicles for a given direction.
    """
    q = 0
    if include_left_forward:
        q += count_waiting_vehicles(cars, direction, "left")
        q += count_waiting_vehicles(cars, direction, "forward")
    if include_right:
        q += count_waiting_vehicles(cars, direction, "right")
    return q

# Phase configuration mapping reduces repeated code:
PHASE_CONFIG = {
    "NS_MAIN": {"directions": ["north", "south"], "include_left_forward": True, "include_right": False},
    "NS_RIGHT": {"directions": ["north", "south"], "include_left_forward": False, "include_right": True},
    "EW_MAIN": {"directions": ["east", "west"], "include_left_forward": True, "include_right": False},
    "EW_RIGHT": {"directions": ["east", "west"], "include_left_forward": False, "include_right": True},
}

def compute_phase_queue(phase_name: str, cars: List) -> int:
    """
    Computes the total queue size for a given phase by summing the queues 
    for all relevant directions.
    """
    config = PHASE_CONFIG.get(phase_name, {})
    return sum(
        get_total_queue(cars, direction, config.get("include_left_forward", True), config.get("include_right", True))
        for direction in config.get("directions", [])
    )

def compute_phase_priority(phase_name: str, cars: List) -> float:
    """
    Compute a priority score for the phase based on its current queue and 
    how long it has not been served.
    """
    now = get_time_since_start()
    time_since_serve = now - last_serve_time[phase_name]
    queue_size = compute_phase_queue(phase_name, cars)
    alpha = 0.5  # weight for waiting time factor; tune as needed
    return queue_size + alpha * (time_since_serve / 10.0)

# Map phase names to their corresponding service functions.
PHASE_SERVE_FUNCTIONS = {}

async def run_adaptive_traffic_loop(controller: TrafficLightController, cars: List) -> None:
    """
    Continuously choose and serve the most urgent phase based on queue lengths 
    and time since the phase was last served. The green time is dynamically adjusted.
    """
    global last_serve_time
    # Initialize last serve times for all phases
    for phase in last_serve_time:
        last_serve_time[phase] = get_time_since_start()

    # Define timing parameters (in seconds)
    MIN_GREEN = 5.0
    MAX_GREEN = 30.0
    EXTEND_STEP = 5.0

    while True:
        # Calculate priority for each phase
        phases = list(PHASE_CONFIG.keys())
        scored_phases = [(phase, compute_phase_priority(phase, cars)) for phase in phases]
        scored_phases.sort(key=lambda x: x[1], reverse=True)
        chosen_phase = scored_phases[0][0]

        # Estimate initial green time: 2 seconds per waiting car
        queue_size = compute_phase_queue(chosen_phase, cars)
        base_duration = 2.0 * queue_size
        duration = max(MIN_GREEN, min(base_duration, MAX_GREEN))

        # Serve the chosen phase
        serve_func = PHASE_SERVE_FUNCTIONS.get(chosen_phase)
        if serve_func:
            await serve_func(controller, duration)
        else:
            continue

        last_serve_time[chosen_phase] = get_time_since_start()

        # Optionally extend green time if the queue is still high
        extended_time = 0.0
        while True:
            current_queue = compute_phase_queue(chosen_phase, cars)
            if current_queue >= queue_size * 0.5 and (duration + extended_time < MAX_GREEN):
                extend_block = min(EXTEND_STEP, MAX_GREEN - (duration + extended_time))
                await serve_func(controller, extend_block)
                extended_time += extend_block
                last_serve_time[chosen_phase] = get_time_since_start()
            else:
                break

# --------------------------------------------------------
# Phase Serving Functions (largely unchanged)
async def serve_ns_main(controller: TrafficLightController, duration: float) -> None:
    from .adaptive_controller import set_all_red
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)
    # Set north-south main green and others red
    controller.trafficLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.RED.value: False, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: True
    }
    controller.trafficLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.RED.value: False, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: True
    }
    controller.trafficLightStates[Direction.EAST.value] = {
        TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False
    }
    controller.trafficLightStates[Direction.WEST.value] = {
        TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False
    }
    # Disable right-turn signals
    for d in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
        controller.rightTurnLightStates[d.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    await controller._broadcast_state()
    await asyncio.sleep(duration / controller.simulationSpeedMultiplier)
    # Transition to amber
    controller.trafficLightStates[Direction.NORTH.value][TrafficLightSignal.GREEN.value] = False
    controller.trafficLightStates[Direction.NORTH.value][TrafficLightSignal.AMBER.value] = True
    controller.trafficLightStates[Direction.SOUTH.value][TrafficLightSignal.GREEN.value] = False
    controller.trafficLightStates[Direction.SOUTH.value][TrafficLightSignal.AMBER.value] = True
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)

async def serve_ns_right(controller: TrafficLightController, duration: float) -> None:
    from .adaptive_controller import set_all_red
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)
    # Enable right-turn signals for north and south only
    controller.rightTurnLightStates[Direction.NORTH.value] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
    controller.rightTurnLightStates[Direction.SOUTH.value] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
    # Keep main signals red
    for d in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
        controller.trafficLightStates[d.value] = {TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False}
    await controller._broadcast_state()
    await asyncio.sleep(duration / controller.simulationSpeedMultiplier)
    # Turn off right-turn signals
    controller.rightTurnLightStates[Direction.NORTH.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    controller.rightTurnLightStates[Direction.SOUTH.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    await controller._broadcast_state()
    await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)

async def serve_ew_main(controller: TrafficLightController, duration: float) -> None:
    from .adaptive_controller import set_all_red
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)
    # Enable east-west main green
    controller.trafficLightStates[Direction.EAST.value] = {TrafficLightSignal.RED.value: False, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: True}
    controller.trafficLightStates[Direction.WEST.value] = {TrafficLightSignal.RED.value: False, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: True}
    controller.trafficLightStates[Direction.NORTH.value] = {TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False}
    controller.trafficLightStates[Direction.SOUTH.value] = {TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False}
    # Disable right-turn signals
    for d in [Direction.EAST, Direction.WEST, Direction.NORTH, Direction.SOUTH]:
        controller.rightTurnLightStates[d.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    await controller._broadcast_state()
    await asyncio.sleep(duration / controller.simulationSpeedMultiplier)
    # Transition to amber for east and west
    controller.trafficLightStates[Direction.EAST.value][TrafficLightSignal.GREEN.value] = False
    controller.trafficLightStates[Direction.EAST.value][TrafficLightSignal.AMBER.value] = True
    controller.trafficLightStates[Direction.WEST.value][TrafficLightSignal.GREEN.value] = False
    controller.trafficLightStates[Direction.WEST.value][TrafficLightSignal.AMBER.value] = True
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)

async def serve_ew_right(controller: TrafficLightController, duration: float) -> None:
    from .adaptive_controller import set_all_red
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)
    # Enable right-turn signals for east and west only
    controller.rightTurnLightStates[Direction.EAST.value] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
    controller.rightTurnLightStates[Direction.WEST.value] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
    # Keep all main signals red
    for d in [Direction.EAST, Direction.WEST, Direction.NORTH, Direction.SOUTH]:
        controller.trafficLightStates[d.value] = {TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False}
    await controller._broadcast_state()
    await asyncio.sleep(duration / controller.simulationSpeedMultiplier)
    # Turn off right-turn signals
    controller.rightTurnLightStates[Direction.EAST.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    controller.rightTurnLightStates[Direction.WEST.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    await controller._broadcast_state()
    await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)

def set_all_red(controller: TrafficLightController):
    """
    Helper: Set all main signals to red and all right-turn signals off.
    """
    for d in [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]:
        controller.trafficLightStates[d.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }
        controller.rightTurnLightStates[d.value] = {
            TrafficLightSignal.OFF.value: True,
            TrafficLightSignal.ON.value: False
        }

# Populate the mapping with the serve functions
PHASE_SERVE_FUNCTIONS.update({
    "NS_MAIN": serve_ns_main,
    "NS_RIGHT": serve_ns_right,
    "EW_MAIN": serve_ew_main,
    "EW_RIGHT": serve_ew_right,
})
