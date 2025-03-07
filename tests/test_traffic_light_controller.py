import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import math
#import asyncio
import pytest
from backend.junction_objects.traffic_light_controller import TrafficLightController
from backend.junction_objects.enums import Direction, TrafficLightSignal

def test_initial_state():
    """Verify that a newly created TrafficLightController has the correct default values."""
    controller = TrafficLightController()
    
    # Check default simulation parameters.
    assert controller.simulationSpeedMultiplier == 1.0, "Simulation speed multiplier should default to 1.0."
    assert controller.use_default_traffic_settings is False, "Default traffic settings flag should be False."
    assert controller.vehicle_data is None, "vehicle_data should be None initially."
    assert controller.junction_settings is None, "junction_settings should be None initially."
    assert controller.traffic_settings is None, "traffic_settings should be None initially."
    
    # Check default traffic light states.
    for d in [Direction.NORTH.value, Direction.EAST.value, Direction.SOUTH.value, Direction.WEST.value]:
        expected_traffic = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }
        expected_right = {
            TrafficLightSignal.OFF.value: True,
            TrafficLightSignal.ON.value: False
        }
        expected_pedestrian = {
            TrafficLightSignal.OFF.value: True,
            TrafficLightSignal.ON.value: False
        }
        assert controller.trafficLightStates[d] == expected_traffic, f"Traffic lights for {d} did not initialize correctly."
        assert controller.rightTurnLightStates[d] == expected_right, f"Right-turn lights for {d} did not initialize correctly."
        assert controller.pedestrianLightStates[d] == expected_pedestrian, f"Pedestrian lights for {d} did not initialize correctly."

def test_update_traffic_settings_default():
    """Test that when traffic-light-enable is off, sequence lengths are reset to 0."""
    controller = TrafficLightController()
    traffic_settings = {"traffic-light-enable": False}
    controller.update_traffic_settings(traffic_settings, use_default=False)
    
    assert controller.VERTICAL_SEQUENCE_LENGTH == 0, "Vertical sequence length should be 0 when traffic lights are disabled."
    assert controller.HORIZONTAL_SEQUENCE_LENGTH == 0, "Horizontal sequence length should be 0 when traffic lights are disabled."
    assert controller.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH == 0, "Vertical right-turn sequence length should be 0 when traffic lights are disabled."
    assert controller.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH == 0, "Horizontal right-turn sequence length should be 0 when traffic lights are disabled."

def test_update_traffic_settings_enabled():
    """Test that enabling traffic lights correctly updates the sequence lengths."""
    controller = TrafficLightController()
    traffic_settings = {
        "traffic-light-enable": True,
        "sequences": 2,  # We'll divide the values by this number.
        "vertical_main_green": 10,
        "horizontal_main_green": 20,
        "vertical_right_green": 4,
        "horizontal_right_green": 6,
    }
    controller.update_traffic_settings(traffic_settings, use_default=False)
    
    # Check that the sequence lengths are computed as expected.
    assert controller.VERTICAL_SEQUENCE_LENGTH == 10 / 2, "Incorrect vertical main green sequence length."
    assert controller.HORIZONTAL_SEQUENCE_LENGTH == 20 / 2, "Incorrect horizontal main green sequence length."
    assert controller.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH == 4 / 2, "Incorrect vertical right-turn sequence length."
    assert controller.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH == 6 / 2, "Incorrect horizontal right-turn sequence length."

def test_update_vehicle_data():
    """Ensure that updating vehicle data stores the new data correctly."""
    controller = TrafficLightController()
    vehicle_info = {"car_count": 5, "types": ["sedan", "truck"]}
    controller.update_vehicle_data(vehicle_info)
    assert controller.vehicle_data == vehicle_info, "Vehicle data was not updated correctly."

def test_update_junction_settings():
    """Check that junction settings are updated and pedestrian data is extracted correctly."""
    controller = TrafficLightController()
    settings = {"pedestrian_duration": 5, "pedestrian_frequency": 10}
    controller.update_junction_settings(settings)
    
    assert controller.junction_settings == settings, "Junction settings were not updated correctly."
    assert controller.pedestrianDuration == 5, "Pedestrian duration did not update correctly."
    assert controller.pedestrianPerMinute == 10, "Pedestrian frequency did not update correctly."

def test_get_pedestrian_data_no_settings():
    """When no junction settings exist, get_pedestrian_data should return (0, 0)."""
    controller = TrafficLightController()
    freq, duration = controller.get_pedestrian_data()
    assert freq == 0, "Pedestrian frequency should be 0 when junction settings are missing."
    assert duration == 0, "Pedestrian duration should be 0 when junction settings are missing."

def test_updateDerivedStates():
    """If any pedestrian light is on, updateDerivedStates should force traffic and right-turn lights to their default off states."""
    controller = TrafficLightController()
    
    # Simulate that the north pedestrian light is on.
    controller.pedestrianLightStates[Direction.NORTH.value] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
    # Manually change the north traffic and right-turn lights so we can check if they're reset.
    controller.trafficLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.RED.value: False,
        TrafficLightSignal.AMBER.value: True,
        TrafficLightSignal.GREEN.value: True
    }
    controller.rightTurnLightStates[Direction.NORTH.value] = {
        TrafficLightSignal.OFF.value: False,
        TrafficLightSignal.ON.value: True
    }
    
    controller.updateDerivedStates()
    
    expected_traffic = {TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False}
    expected_right = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    for d in [Direction.NORTH.value, Direction.EAST.value, Direction.SOUTH.value, Direction.WEST.value]:
        assert controller.trafficLightStates[d] == expected_traffic, f"Traffic lights for {d} were not updated correctly after a pedestrian event."
        assert controller.rightTurnLightStates[d] == expected_right, f"Right-turn lights for {d} were not updated correctly after a pedestrian event."

@pytest.mark.asyncio
async def test_broadcast_state():
    """Test that the _broadcast_state method packages the states as JSON and calls the broadcast callback."""
    controller = TrafficLightController()
    messages = []
    
    async def dummy_callback(msg):
        messages.append(msg)
    
    controller.set_broadcast_callback(dummy_callback)
    
    await controller._broadcast_state()
    
    assert len(messages) == 1, "Broadcast callback should have been called exactly once."
    data = json.loads(messages[0])
    for key in ["trafficLightStates", "rightTurnLightStates", "pedestrianLightStates"]:
        assert key in data, f"Broadcasted JSON data is missing the key '{key}'."

def test_get_cycle_times():
    """Check that cycle times are calculated correctly based on gap and sequence lengths."""
    controller = TrafficLightController()
    # For this test, we assign some specific values.
    controller.gap = 1
    controller.VERTICAL_SEQUENCE_LENGTH = 5
    controller.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = 2
    controller.HORIZONTAL_SEQUENCE_LENGTH = 10
    controller.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = 3
    
    # Expected cycle times:
    # verticalCycleTime = (5*gap) + vertical_main_green + vertical_right_green = 5 + 5 + 2 = 12
    # horizontalCycleTime = (5*gap) + horizontal_main_green + horizontal_right_green = 5 + 10 + 3 = 18
    vertical_time, horizontal_time = controller.get_cycle_times()
    assert vertical_time == 12, "Vertical cycle time calculation is incorrect."
    assert horizontal_time == 18, "Horizontal cycle time calculation is incorrect."

def test_get_max_gaps_per_minute():
    """Validate that get_max_gaps_per_minute returns the correct number of gaps based on cycle time and pedestrian duration."""
    controller = TrafficLightController()
    controller.gap = 1
    controller.VERTICAL_SEQUENCE_LENGTH = 5
    controller.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = 2
    controller.HORIZONTAL_SEQUENCE_LENGTH = 10
    controller.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = 3
    # Set pedestrian duration for the test.
    controller.pedestrianDuration = 4
    
    # From our previous test, verticalCycleTime = 12 and horizontalCycleTime = 18.
    total_cycle_time = 12 + 18 + (2 * 4)  # 12 + 18 + 8 = 38
    expected_max_gaps = 2 * (60 / total_cycle_time)
    
    result = controller.get_max_gaps_per_minute()
    assert math.isclose(result, expected_max_gaps, rel_tol=1e-5), "Maximum gaps per minute calculation is incorrect."