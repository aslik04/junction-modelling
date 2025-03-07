import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
#import random
import pytest
from backend.junction_objects.traffic_light_state import (
    run_vertical_sequence,
    run_horizontal_sequence,
    run_pedestrian_event,
    run_traffic_loop,
)
from backend.junction_objects.traffic_light_controller import TrafficLightController
from backend.junction_objects.enums import Direction, TrafficLightSignal

class DummyBroadcast:
    """
    A dummy broadcast callback that simply records any messages
    so we can verify that state updates (broadcasts) are occurring.
    """
    def __init__(self):
        self.messages = []

    async def callback(self, message: str):
        self.messages.append(message)

@pytest.fixture
def controller_and_broadcast():
    """
    Create a TrafficLightController instance configured for fast tests,
    and attach a dummy broadcast callback.
    """
    ctrl = TrafficLightController()
    ctrl.simulationSpeedMultiplier = 100.0  # Speed up sleep durations.
    ctrl.gap = 0.001  # Use a very short gap for testing.
    dummy = DummyBroadcast()
    ctrl.set_broadcast_callback(dummy.callback)
    return ctrl, dummy

@pytest.mark.asyncio
async def test_run_vertical_sequence(controller_and_broadcast):
    """Test the vertical sequence to verify that light states end up as expected."""
    controller, dummy = controller_and_broadcast
    # Set non-zero sequence lengths to trigger the vertical sequence branch.
    controller.VERTICAL_SEQUENCE_LENGTH = 0.01
    controller.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = 0.01

    # Ensure right-turn lights for EAST and WEST are off so the initial while loop does not block.
    controller.rightTurnLightStates[Direction.EAST.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    controller.rightTurnLightStates[Direction.WEST.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }

    # Run the vertical sequence.
    await run_vertical_sequence(controller)

    # Final expected traffic state for NORTH and SOUTH: red (with amber and green off).
    expected_traffic = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    assert controller.trafficLightStates[Direction.NORTH.value] == expected_traffic, (
        "NORTH traffic lights did not end up red after vertical sequence."
    )
    assert controller.trafficLightStates[Direction.SOUTH.value] == expected_traffic, (
        "SOUTH traffic lights did not end up red after vertical sequence."
    )

    # Final expected right-turn state for NORTH and SOUTH: off.
    expected_right = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    assert controller.rightTurnLightStates[Direction.NORTH.value] == expected_right, (
        "NORTH right-turn lights were not reset after vertical sequence."
    )
    assert controller.rightTurnLightStates[Direction.SOUTH.value] == expected_right, (
        "SOUTH right-turn lights were not reset after vertical sequence."
    )

    # Verify that broadcast messages were sent during the sequence.
    assert len(dummy.messages) > 0, "No broadcast messages were sent during vertical sequence."

@pytest.mark.asyncio
async def test_run_horizontal_sequence(controller_and_broadcast):
    """Test the horizontal sequence and verify the final states of east and west lights."""
    controller, dummy = controller_and_broadcast
    # Set non-zero sequence lengths to ensure the horizontal sequence runs.
    controller.HORIZONTAL_SEQUENCE_LENGTH = 0.01
    controller.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = 0.01

    # Ensure right-turn lights for NORTH and SOUTH are off so the while loop does not block.
    controller.rightTurnLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    controller.rightTurnLightStates[Direction.SOUTH.value] = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }

    # Run the horizontal sequence.
    await run_horizontal_sequence(controller)

    # The final expected state for EAST and WEST traffic lights should be red.
    expected_traffic = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    assert controller.trafficLightStates[Direction.EAST.value] == expected_traffic, (
        "EAST traffic lights did not end up red after horizontal sequence."
    )
    assert controller.trafficLightStates[Direction.WEST.value] == expected_traffic, (
        "WEST traffic lights did not end up red after horizontal sequence."
    )

    # The final expected right-turn state for EAST and WEST should be off.
    expected_right = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    assert controller.rightTurnLightStates[Direction.EAST.value] == expected_right, (
        "EAST right-turn lights were not reset after horizontal sequence."
    )
    assert controller.rightTurnLightStates[Direction.WEST.value] == expected_right, (
        "WEST right-turn lights were not reset after horizontal sequence."
    )

    # Verify that broadcast messages were sent.
    assert len(dummy.messages) > 0, "No broadcast messages were sent during horizontal sequence."

@pytest.mark.asyncio
async def test_run_pedestrian_event(controller_and_broadcast):
    """Test the pedestrian event to ensure pedestrian lights are toggled correctly."""
    controller, dummy = controller_and_broadcast
    # Set pedestrian duration to a very short interval for testing.
    controller.pedestrianDuration = 0.01

    # Run the pedestrian event.
    await run_pedestrian_event(controller)

    # After the event, pedestrian lights for all directions should be off.
    expected_pedestrian = {
        TrafficLightSignal.OFF.value: True,
        TrafficLightSignal.ON.value: False
    }
    for d in [Direction.NORTH.value, Direction.EAST.value, Direction.SOUTH.value, Direction.WEST.value]:
        assert controller.pedestrianLightStates[d] == expected_pedestrian, (
            f"Pedestrian light state for {d} was not reset after pedestrian event."
        )

    # Also verify that the traffic lights were set to red during the event.
    expected_traffic = {
        TrafficLightSignal.RED.value: True,
        TrafficLightSignal.AMBER.value: False,
        TrafficLightSignal.GREEN.value: False
    }
    for d in [Direction.NORTH.value, Direction.EAST.value, Direction.SOUTH.value, Direction.WEST.value]:
        assert controller.trafficLightStates[d] == expected_traffic, (
            f"Traffic light state for {d} is not red during pedestrian event."
        )

@pytest.mark.asyncio
async def test_run_traffic_loop(controller_and_broadcast):
    """
    Run the main traffic loop briefly and verify that state broadcasts occur.
    Since the loop is infinite, we cancel it after a short period.
    """
    controller, dummy = controller_and_broadcast
    # Configure the controller with small time intervals to make the test run fast.
    controller.gap = 0.001
    controller.simulationSpeedMultiplier = 100.0
    controller.VERTICAL_SEQUENCE_LENGTH = 0.01
    controller.HORIZONTAL_SEQUENCE_LENGTH = 0.01
    controller.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = 0.01
    controller.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = 0.01
    controller.pedestrianDuration = 0.01
    controller.pedestrianPerMinute = 0  # Prevent random pedestrian events for predictable behavior

    # Start the traffic loop in a background task.
    loop_task = asyncio.create_task(run_traffic_loop(controller))
    # Let the loop run briefly.
    await asyncio.sleep(0.1)
    # Cancel the loop task.
    loop_task.cancel()
    try:
        await loop_task
    except asyncio.CancelledError:
        pass

    # Verify that some broadcast messages were sent during the loop.
    assert len(dummy.messages) > 0, "Traffic loop did not broadcast any state updates."