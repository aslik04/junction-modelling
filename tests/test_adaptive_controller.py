import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import math
import pytest
from backend.junction_objects.adaptive_controller import (
    get_vertical_wait_count,
    get_horizontal_wait_count,
    get_vertical_right_wait_count,
    get_horizontal_right_wait_count,
    nonlinear_green,
    set_phase,
    run_right_turn_phase,
    run_pedestrian_event,
    run_adaptive_traffic_loop,
)

# These dummy classes simulate the minimal behavior required by the adaptive controller tests.
class DummyCar:
    """A simple dummy car to test the wait count functions."""
    def __init__(self, inital_direction, passedStopLine, turn_type):
        self.inital_direction = inital_direction
        self.passedStopLine = passedStopLine
        self.turn_type = turn_type

class DummyController:
    """A dummy controller mimicking the traffic light controller used in the adaptive system."""
    def __init__(self):
        self.trafficLightStates = {d: {} for d in ["north", "east", "south", "west"]}
        self.rightTurnLightStates = {d: {} for d in ["north", "east", "south", "west"]}
        self.pedestrianLightStates = {d: {} for d in ["north", "east", "south", "west"]}
        # Speed multiplier is set high to speed up sleep calls in tests.
        self.simulationSpeedMultiplier = 10.0  
        self.pedestrianDuration = 0.5
        # For testing adaptive loop, setting pedestrian events per minute to 0 to simplify.
        self.pedestrianPerMinute = 0  
        self.broadcast_log = []

    async def _broadcast_state(self):
        # Instead of updating any UI, we log that a broadcast happened.
        self.broadcast_log.append("broadcasted")

# ----- Counting Functions Tests -----

def test_get_vertical_wait_count():
    # Only count vertical cars (north/south) that haven't passed the stop line and aren't turning right.
    cars = [
        DummyCar("north", False, "forward"),
        DummyCar("south", False, "left"),
        DummyCar("north", True, "forward"),  # Should not be counted.
        DummyCar("north", False, "right"),   # Should not be counted.
        DummyCar("east", False, "forward"),  # Not vertical.
    ]
    count = get_vertical_wait_count(cars)
    assert count == 2, "Expected only two vertical cars to be waiting."

def test_get_horizontal_wait_count():
    # Only count horizontal cars (east/west) that meet the criteria.
    cars = [
        DummyCar("east", False, "forward"),
        DummyCar("west", False, "left"),
        DummyCar("east", True, "forward"),   # Already passed stop line.
        DummyCar("west", False, "right"),    # Turning right.
        DummyCar("north", False, "forward"), # Not horizontal.
    ]
    count = get_horizontal_wait_count(cars)
    assert count == 2, "Expected only two horizontal cars to be waiting."

def test_get_vertical_right_wait_count():
    # Count vertical cars turning right.
    cars = [
        DummyCar("north", False, "right"),
        DummyCar("south", False, "right"),
        DummyCar("north", True, "right"),    # Should be ignored.
        DummyCar("south", False, "forward"), # Not a right turn.
    ]
    count = get_vertical_right_wait_count(cars)
    assert count == 2, "Expected two vertical cars waiting for right turn."

def test_get_horizontal_right_wait_count():
    # Count horizontal cars turning right.
    cars = [
        DummyCar("east", False, "right"),
        DummyCar("west", False, "right"),
        DummyCar("east", True, "right"),     # Should be ignored.
        DummyCar("west", False, "forward"),  # Not a right turn.
    ]
    count = get_horizontal_right_wait_count(cars)
    assert count == 2, "Expected two horizontal cars waiting for right turn."

def test_nonlinear_green():
    # Validate the nonlinear_green calculation.
    min_green = 2.0
    max_green = 20.0
    k = 2.0
    count = 5
    expected = min_green + (max_green - min_green) * (count / (count + k))
    result = nonlinear_green(count, min_green, max_green, k)
    assert math.isclose(result, expected, rel_tol=1e-5), "nonlinear_green function did not return the expected value."

# ----- Asynchronous Function Tests -----

@pytest.mark.asyncio
async def test_set_phase_vertical():
    """Test that setting the phase to 'vertical' updates the traffic lights as expected."""
    controller = DummyController()
    await set_phase(controller, "vertical")
    assert controller.trafficLightStates["north"] == {"red": False, "amber": False, "green": True}, "North traffic light state is incorrect."
    assert controller.trafficLightStates["south"] == {"red": False, "amber": False, "green": True}, "South traffic light state is incorrect."
    assert controller.trafficLightStates["east"] == {"red": True, "amber": False, "green": False}, "East should be red."
    assert controller.trafficLightStates["west"] == {"red": True, "amber": False, "green": False}, "West should be red."
    assert len(controller.broadcast_log) >= 1, "Expected a broadcast after setting the phase."

@pytest.mark.asyncio
async def test_set_phase_horizontal():
    """Ensure horizontal phase correctly updates east and west to green."""
    controller = DummyController()
    await set_phase(controller, "horizontal")
    assert controller.trafficLightStates["east"] == {"red": False, "amber": False, "green": True}, "East light should be green."
    assert controller.trafficLightStates["west"] == {"red": False, "amber": False, "green": True}, "West light should be green."
    assert controller.trafficLightStates["north"] == {"red": True, "amber": False, "green": False}, "North light should be red."
    assert controller.trafficLightStates["south"] == {"red": True, "amber": False, "green": False}, "South light should be red."

@pytest.mark.asyncio
async def test_set_phase_red():
    """Test that the red phase sets all traffic lights to red."""
    controller = DummyController()
    await set_phase(controller, "red")
    for d in ["north", "east", "south", "west"]:
        assert controller.trafficLightStates[d] == {"red": True, "amber": False, "green": False}, f"{d.capitalize()} light should be red."

@pytest.mark.asyncio
async def test_run_right_turn_phase():
    """Check that the right-turn phase correctly toggles the right-turn lights."""
    controller = DummyController()
    directions = ["north", "south"]
    phase_time = 0.1
    transition_time = 0.1
    await run_right_turn_phase(controller, directions, phase_time, controller.simulationSpeedMultiplier, transition_time)
    for d in directions:
        assert controller.rightTurnLightStates[d] == {"off": True, "on": False}, f"Right-turn light for {d} should be off after phase."
    assert len(controller.broadcast_log) >= 2, "Expected multiple broadcasts during the right-turn phase."

@pytest.mark.asyncio
async def test_run_pedestrian_event():
    """Ensure the pedestrian event sets pedestrian lights correctly and then turns them off."""
    controller = DummyController()
    await run_pedestrian_event(controller)
    for d in ["north", "east", "south", "west"]:
        # After the event, pedestrian lights should be off.
        assert controller.pedestrianLightStates[d] == {"off": True, "on": False}, f"Pedestrian light for {d} should be off after event."
        # Also, traffic lights should be set to red.
        assert controller.trafficLightStates[d] == {"red": True, "amber": False, "green": False}, f"Traffic light for {d} should be red during pedestrian event."

@pytest.mark.asyncio
async def test_run_adaptive_traffic_loop():
    """Run the adaptive loop briefly and check that state broadcasts are occurring."""
    controller = DummyController()
    # Increase simulation speed so that the test runs quickly.
    controller.simulationSpeedMultiplier = 100.0
    cars = []  # No waiting cars in this test scenario.
    # Start the adaptive loop in a background task.
    task = asyncio.create_task(run_adaptive_traffic_loop(controller, cars, gap=0.001))
    # Let the loop run for a short period.
    await asyncio.sleep(0.2)
    task.cancel()  # Cancel to avoid an infinite loop.
    try:
        await task
    except asyncio.CancelledError:
        pass
    # We expect at least one broadcast during the short run.
    assert len(controller.broadcast_log) > 0, "Adaptive loop did not broadcast any state updates."