import asyncio
import math
import random
from typing import List
from junction_objects.traffic_light_controller import TrafficLightController
from junction_objects.enums import Direction, TrafficLightSignal
from junction_objects.vehicle_stop_line import has_crossed_line

# --------------------------------------------------------
# Helper to count waiting vehicles for each direction/turn
# --------------------------------------------------------
def count_waiting_vehicles(cars: List, direction: str, turn_type: str, stop_threshold: float = 50.0) -> int:
    """
    Counts how many vehicles in 'cars' are in the given direction and turn type,
    and are still near the stop line (i.e. have not yet crossed it) and are within
    a certain distance threshold.
    """
    count = 0
    for c in cars:
        if c.inital_direction == direction and c.turn_type == turn_type:
            # Instead of checking a missing attribute, use has_crossed_line(c)
            # If the car has not crossed the stop line and is within the threshold, count it.
            if not has_crossed_line(c) and getattr(c, "distance_to_intersection", 0) < stop_threshold:
                count += 1
    return count

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

# --------------------------------------------------------
# Main Adaptive Traffic Control Loop
# --------------------------------------------------------
async def run_adaptive_traffic_loop(controller: TrafficLightController, cars: List) -> None:
    """
    Continuously adjusts which phase (N-S main, N-S right, E-W main, E-W right) gets green,
    based on the highest queue of waiting vehicles.
    """
    while True:
        ns_main_queue = (get_total_queue(cars, direction="north", include_left_forward=True, include_right=False) +
                         get_total_queue(cars, direction="south", include_left_forward=True, include_right=False))
        ns_right_queue = (get_total_queue(cars, direction="north", include_left_forward=False, include_right=True) +
                          get_total_queue(cars, direction="south", include_left_forward=False, include_right=True))
        ew_main_queue = (get_total_queue(cars, direction="east", include_left_forward=True, include_right=False) +
                         get_total_queue(cars, direction="west", include_left_forward=True, include_right=False))
        ew_right_queue = (get_total_queue(cars, direction="east", include_left_forward=False, include_right=True) +
                          get_total_queue(cars, direction="west", include_left_forward=False, include_right=True))

        print(f"[ADAPTIVE] ns_main={ns_main_queue}, ns_right={ns_right_queue}, ew_main={ew_main_queue}, ew_right={ew_right_queue}")


        phases = [
            {"name": "NS_MAIN", "queue": ns_main_queue},
            {"name": "NS_RIGHT", "queue": ns_right_queue},
            {"name": "EW_MAIN", "queue": ew_main_queue},
            {"name": "EW_RIGHT", "queue": ew_right_queue},
        ]
        
        phases.sort(key=lambda p: p["queue"], reverse=True)
        chosen_phase = phases[0]["name"]
        chosen_queue = phases[0]["queue"]

        if chosen_queue == 0:
            # If no cars are waiting, run a short green for N-S main as default.
            await serve_ns_main(controller, duration=5.0)
            continue

        serve_time = min(2.0 * chosen_queue, 20.0)  # 2 seconds per vehicle, capped at 20 seconds

        if chosen_phase == "NS_MAIN":
            await serve_ns_main(controller, serve_time)
        elif chosen_phase == "NS_RIGHT":
            await serve_ns_right(controller, serve_time)
        elif chosen_phase == "EW_MAIN":
            await serve_ew_main(controller, serve_time)
        elif chosen_phase == "EW_RIGHT":
            await serve_ew_right(controller, serve_time)

        print(f"[ADAPTIVE] chosen phase={chosen_phase}, queue={chosen_queue}")


# --------------------------------------------------------
# Phase Serving Helpers
# --------------------------------------------------------
async def serve_ns_main(controller: TrafficLightController, duration: float) -> None:
    """
    Turn North & South main signals green (forward/left),
    keep East & West red. We'll do a minimal red-amber-green cycle for correctness.
    """
    # 1) Clear all for safety
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)  # short all-red

    # 2) Turn N-S to GREEN, E-W stays RED
    controller.trafficLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.RED.value: False,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: True
    }
    controller.trafficLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.RED.value: False,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: True
    }
    # Ensure E-W is red
    controller.trafficLightStates[Direction.EAST.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    controller.trafficLightStates[Direction.WEST.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    # Right-turn lights for N-S off
    controller.rightTurnLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    controller.rightTurnLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    # Right-turn lights for E-W off
    controller.rightTurnLightStates[Direction.EAST.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    controller.rightTurnLightStates[Direction.WEST.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    
    await controller._broadcast_state()

    # 3) Keep green for 'duration'
    await asyncio.sleep(duration / controller.simulationSpeedMultiplier)

    # 4) Turn amber for N-S
    controller.trafficLightStates[Direction.NORTH.value][TrafficLightSignal.GREEN.value] = False
    controller.trafficLightStates[Direction.NORTH.value][TrafficLightSignal.AMBER.value] = True
    controller.trafficLightStates[Direction.SOUTH.value][TrafficLightSignal.GREEN.value] = False
    controller.trafficLightStates[Direction.SOUTH.value][TrafficLightSignal.AMBER.value] = True
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)  # 1s amber
    
    # 5) Then back to red
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)  # short gap

async def serve_ns_right(controller: TrafficLightController, duration: float) -> None:
    # Similar logic, but specifically turn on N-S right-turn arrows
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)

    # N-S right-turn on
    controller.rightTurnLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.OFF.value: False,
        TrafficLightSignal.ON.value: True
    }
    controller.rightTurnLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.OFF.value: False,
        TrafficLightSignal.ON.value: True
    }
    # Keep main signals red
    controller.trafficLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    controller.trafficLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    controller.trafficLightStates[Direction.EAST.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    controller.trafficLightStates[Direction.WEST.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    await controller._broadcast_state()

    await asyncio.sleep(duration / controller.simulationSpeedMultiplier)

    # Turn off
    controller.rightTurnLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    controller.rightTurnLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    await controller._broadcast_state()
    await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)

async def serve_ew_main(controller: TrafficLightController, duration: float) -> None:
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)

    # Turn E-W green
    controller.trafficLightStates[Direction.EAST.value] = {
        TrafficLightSignal.RED.value: False,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: True
    }
    controller.trafficLightStates[Direction.WEST.value] = {
        TrafficLightSignal.RED.value: False,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: True
    }
    controller.trafficLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    controller.trafficLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    # Right-turn lights off
    controller.rightTurnLightStates[Direction.EAST.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    controller.rightTurnLightStates[Direction.WEST.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    controller.rightTurnLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    controller.rightTurnLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    await controller._broadcast_state()

    await asyncio.sleep(duration / controller.simulationSpeedMultiplier)

    # Amber
    controller.trafficLightStates[Direction.EAST.value][TrafficLightSignal.GREEN.value] = False
    controller.trafficLightStates[Direction.EAST.value][TrafficLightSignal.AMBER.value] = True
    controller.trafficLightStates[Direction.WEST.value][TrafficLightSignal.GREEN.value] = False
    controller.trafficLightStates[Direction.WEST.value][TrafficLightSignal.AMBER.value] = True
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)

    # Red
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)

async def serve_ew_right(controller: TrafficLightController, duration: float) -> None:
    set_all_red(controller)
    await controller._broadcast_state()
    await asyncio.sleep(1.0 / controller.simulationSpeedMultiplier)

    # E-W right-turn on
    controller.rightTurnLightStates[Direction.EAST.value] = {
        TrafficLightSignal.OFF.value: False,
        TrafficLightSignal.ON.value: True
    }
    controller.rightTurnLightStates[Direction.WEST.value] = {
        TrafficLightSignal.OFF.value: False,
        TrafficLightSignal.ON.value: True
    }
    # Keep main signals red
    controller.trafficLightStates[Direction.EAST.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    controller.trafficLightStates[Direction.WEST.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    controller.trafficLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    controller.trafficLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    await controller._broadcast_state()

    await asyncio.sleep(duration / controller.simulationSpeedMultiplier)

    # Turn off
    controller.rightTurnLightStates[Direction.EAST.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    controller.rightTurnLightStates[Direction.WEST.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    await controller._broadcast_state()
    await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)

def set_all_red(controller: TrafficLightController):
    """
    Helper: set all main signals red, all right-turn signals off.
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
