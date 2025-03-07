import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import math
import pytest
from backend.junction_objects.enums import Direction, TurnType
from backend.junction_objects.vehicle import Car

# Define a sample junctionData fixture with assumed values
@pytest.fixture
def junction_data():
    return {
        "numOfLanes": 3,
        "widthOfCar": 2.0,
        "heightOfCar": 4.0,
        "leftVertical": 10,
        "topHorizontal": 20,
        "rightVertical": 50,
        "bottomHorizontal": 60,
        "canvasHeight": 100,
        "canvasWidth": 120,
        "pixelWidthOfLane": 3.0
    }

def test_car_initialization_north(junction_data):
    lane = 1
    speed = 30.0
    car = Car(Direction.NORTH, lane, speed, TurnType.FORWARD, junction_data)
    
    expected_x = junction_data["leftVertical"] + junction_data["pixelWidthOfLane"] * (lane + 0.5)
    expected_y = junction_data["canvasHeight"] + junction_data["heightOfCar"]
    
    assert car.x == expected_x
    assert car.y == expected_y
    assert car.rightTurnInitialAngle == 0.0
    # For FORWARD, lane should remain as provided.
    assert car.lane == lane

def test_car_initialization_east(junction_data):
    lane = 0
    speed = 25.0
    car = Car(Direction.EAST, lane, speed, TurnType.FORWARD, junction_data)
    
    expected_x = -junction_data["widthOfCar"]
    expected_y = junction_data["topHorizontal"] + junction_data["pixelWidthOfLane"] * (lane + 0.5)
    
    assert car.x == expected_x
    assert car.y == expected_y
    assert math.isclose(car.rightTurnInitialAngle, math.pi / 2)
    assert car.lane == lane

def test_car_initialization_south(junction_data):
    lane = 2
    speed = 40.0
    car = Car(Direction.SOUTH, lane, speed, TurnType.FORWARD, junction_data)
    
    expected_x = junction_data["rightVertical"] - junction_data["pixelWidthOfLane"] * (lane + 0.5)
    expected_y = -junction_data["heightOfCar"]
    
    assert car.x == expected_x
    assert car.y == expected_y
    assert math.isclose(car.rightTurnInitialAngle, math.pi)
    assert car.lane == lane

def test_car_initialization_west(junction_data):
    lane = 1
    speed = 35.0
    car = Car(Direction.WEST, lane, speed, TurnType.FORWARD, junction_data)
    
    expected_x = junction_data["canvasWidth"] + junction_data["widthOfCar"]
    expected_y = junction_data["bottomHorizontal"] - junction_data["pixelWidthOfLane"] * (lane + 0.5)
    
    assert car.x == expected_x
    assert car.y == expected_y
    assert math.isclose(car.rightTurnInitialAngle, -math.pi / 2)
    assert car.lane == lane

def test_car_left_turn_sets_lane_zero(junction_data):
    lane = 2  # Any initial lane provided
    speed = 30.0
    car = Car(Direction.NORTH, lane, speed, TurnType.LEFT, junction_data)
    # For a left turn, lane should be forced to 0.
    assert car.lane == 0

def test_car_right_turn_sets_lane_max(junction_data):
    initial_lane = 0  # Arbitrary initial lane
    speed = 30.0
    car = Car(Direction.NORTH, initial_lane, speed, TurnType.RIGHT, junction_data)
    # For a right turn, lane should be set to numOfLanes - 1.
    assert car.lane == junction_data["numOfLanes"] - 1

def test_to_dict(junction_data):
    lane = 1
    speed = 30.0
    car = Car(Direction.NORTH, lane, speed, TurnType.FORWARD, junction_data)
    car_dict = car.to_dict()
    
    expected_keys = {
        "direction", "lane", "speed", "turnType", "x",
        "y", "currentRightTurnAngle", "pngIndex", "width", "height"
    }
    # Check that all expected keys are present.
    assert expected_keys.issubset(car_dict.keys())
    assert car_dict["direction"] == car.direction
    assert car_dict["lane"] == car.lane
    assert car_dict["speed"] == speed
    assert car_dict["turnType"] == car.turn_type
    assert car_dict["width"] == junction_data["widthOfCar"]
    assert car_dict["height"] == junction_data["heightOfCar"]
    # pngIndex is randomly generated, so check it falls in the expected range.
    assert 0 <= car_dict["pngIndex"] <= 4

def test_invalid_direction(junction_data):
    speed = 30.0
    with pytest.raises(ValueError):
        # Passing an invalid direction should raise a ValueError.
        Car("invalid_direction", 1, speed, TurnType.FORWARD, junction_data)