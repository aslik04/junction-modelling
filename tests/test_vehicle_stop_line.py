import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
#import pytest
from backend.junction_objects.vehicle_stop_line import (
    get_stop_line,
    can_pass_stop_line,
    stop_at_stop_line,
    has_crossed_line,
    queue_vehicle,
)
from backend.junction_objects.enums import Direction

# -----------------------------------------------------------------------------
# Helper: A simple dummy car for our tests.
# -----------------------------------------------------------------------------
class DummyCar:
    pass

def create_dummy_car(direction, speed=10, x=50, y=50, lane=0, height=10):
    """
    Creates a dummy car with the attributes required for testing stop-line functions.
    
    The junctionData dictionary is set with sample values:
      - topHorizontal: 0
      - bottomHorizontal: 100
      - leftVertical: 0
      - rightVertical: 100
      - pixelWidthOfLane: 10
      
    With these values, the stop line offset is calculated as:
      offset = 10 * 1.25 + 25 = 37.5
    So, for example, a NORTH-bound car will have stop line at 100 + 37.5 = 137.5.
    """
    car = DummyCar()
    car.direction = direction
    car.speed = speed
    car.x = x
    car.y = y
    car.lane = lane
    car.height = height
    car.junctionData = {
        "topHorizontal": 0,
        "bottomHorizontal": 100,
        "leftVertical": 0,
        "rightVertical": 100,
        "pixelWidthOfLane": 10,
    }
    return car

# -----------------------------------------------------------------------------
# Tests for get_stop_line
# -----------------------------------------------------------------------------
def test_get_stop_line_north():
    car = create_dummy_car(Direction.NORTH)
    # Expected: bottomHorizontal (100) + offset (10*1.25+25 = 37.5) = 137.5
    expected = 137.5
    assert math.isclose(get_stop_line(car), expected, rel_tol=1e-5), "Stop line for NORTH-bound car is incorrect."

def test_get_stop_line_east():
    car = create_dummy_car(Direction.EAST)
    # Expected: leftVertical (0) - offset (37.5) = -37.5
    expected = -37.5
    assert math.isclose(get_stop_line(car), expected, rel_tol=1e-5), "Stop line for EAST-bound car is incorrect."

def test_get_stop_line_south():
    car = create_dummy_car(Direction.SOUTH)
    # Expected: topHorizontal (0) - offset (37.5) = -37.5
    expected = -37.5
    assert math.isclose(get_stop_line(car), expected, rel_tol=1e-5), "Stop line for SOUTH-bound car is incorrect."

def test_get_stop_line_west():
    car = create_dummy_car(Direction.WEST)
    # Expected: rightVertical (100) + offset (37.5) = 137.5
    expected = 137.5
    assert math.isclose(get_stop_line(car), expected, rel_tol=1e-5), "Stop line for WEST-bound car is incorrect."

# -----------------------------------------------------------------------------
# Tests for can_pass_stop_line
# -----------------------------------------------------------------------------
def test_can_pass_stop_line_north_true():
    # For NORTH, condition: (car.y - speed) >= stop_line
    # With stop line = 137.5, if car.y = 150 and speed = 10, then 150 - 10 = 140 >= 137.5 → True.
    car = create_dummy_car(Direction.NORTH, speed=10, y=150)
    assert can_pass_stop_line(car) is True, "North-bound car should be able to pass the stop line."

def test_can_pass_stop_line_north_false():
    # If car.y = 140, then 140 - 10 = 130, which is < 137.5 → False.
    car = create_dummy_car(Direction.NORTH, speed=10, y=140)
    assert can_pass_stop_line(car) is False, "North-bound car should not be able to pass the stop line."

def test_can_pass_stop_line_east_true():
    # For EAST, condition: (car.x + speed) <= stop_line
    # With stop line = -37.5, if car.x = -50 and speed = 10, then -50+10 = -40, which is <= -37.5.
    car = create_dummy_car(Direction.EAST, speed=10, x=-50)
    assert can_pass_stop_line(car) is True, "East-bound car should be able to pass the stop line."

def test_can_pass_stop_line_east_false():
    # If car.x = -30, then -30+10 = -20 which is > -37.5 → False.
    car = create_dummy_car(Direction.EAST, speed=10, x=-30)
    assert can_pass_stop_line(car) is False, "East-bound car should not be able to pass the stop line."

def test_can_pass_stop_line_south_true():
    # For SOUTH, condition: (car.y + speed) <= stop_line.
    # With stop line = -37.5, if car.y = -50 and speed = 10, then -50+10 = -40 <= -37.5.
    car = create_dummy_car(Direction.SOUTH, speed=10, y=-50)
    assert can_pass_stop_line(car) is True, "South-bound car should be able to pass the stop line."

def test_can_pass_stop_line_south_false():
    # If car.y = -20, then -20+10 = -10 > -37.5 → False.
    car = create_dummy_car(Direction.SOUTH, speed=10, y=-20)
    assert can_pass_stop_line(car) is False, "South-bound car should not be able to pass the stop line."

def test_can_pass_stop_line_west_true():
    # For WEST, condition: (car.x - speed) >= stop_line.
    # With stop line = 137.5, if car.x = 150 and speed = 10, then 150-10 = 140 >= 137.5.
    car = create_dummy_car(Direction.WEST, speed=10, x=150)
    assert can_pass_stop_line(car) is True, "West-bound car should be able to pass the stop line."

def test_can_pass_stop_line_west_false():
    # If car.x = 130, then 130-10 = 120 < 137.5 → False.
    car = create_dummy_car(Direction.WEST, speed=10, x=130)
    assert can_pass_stop_line(car) is False, "West-bound car should not be able to pass the stop line."

# -----------------------------------------------------------------------------
# Tests for stop_at_stop_line
# -----------------------------------------------------------------------------
def test_stop_at_stop_line_north():
    car = create_dummy_car(Direction.NORTH, y=200)
    # Before: car.y is 200. After stopping, car.y should be set to stop line for NORTH.
    expected = get_stop_line(car)
    stop_at_stop_line(car)
    assert math.isclose(car.y, expected, rel_tol=1e-5), "stop_at_stop_line did not set y correctly for NORTH-bound car."

def test_stop_at_stop_line_east():
    car = create_dummy_car(Direction.EAST, x=-100)
    expected = get_stop_line(car)
    stop_at_stop_line(car)
    assert math.isclose(car.x, expected, rel_tol=1e-5), "stop_at_stop_line did not set x correctly for EAST-bound car."

def test_stop_at_stop_line_south():
    car = create_dummy_car(Direction.SOUTH, y=-100)
    expected = get_stop_line(car)
    stop_at_stop_line(car)
    assert math.isclose(car.y, expected, rel_tol=1e-5), "stop_at_stop_line did not set y correctly for SOUTH-bound car."

def test_stop_at_stop_line_west():
    car = create_dummy_car(Direction.WEST, x=200)
    expected = get_stop_line(car)
    stop_at_stop_line(car)
    assert math.isclose(car.x, expected, rel_tol=1e-5), "stop_at_stop_line did not set x correctly for WEST-bound car."

# -----------------------------------------------------------------------------
# Tests for has_crossed_line
# -----------------------------------------------------------------------------
def test_has_crossed_line_north():
    # For NORTH, if car.y < stop line, then has_crossed_line returns True.
    car = create_dummy_car(Direction.NORTH, y=130)
    expected_line = get_stop_line(car)  # 137.5
    assert 130 < expected_line, "Test setup error: car.y should be less than stop line."
    assert has_crossed_line(car) is True, "North-bound car with y < stop line should be marked as having crossed."

    car2 = create_dummy_car(Direction.NORTH, y=150)
    assert has_crossed_line(car2) is False, "North-bound car with y >= stop line should not be marked as having crossed."

def test_has_crossed_line_east():
    # For EAST, condition: car.x > stop line.
    car = create_dummy_car(Direction.EAST, x=-20)
    expected_line = get_stop_line(car)  # -37.5
    assert -20 > expected_line, "Test setup error: car.x should be greater than stop line."
    assert has_crossed_line(car) is True, "East-bound car with x > stop line should be marked as having crossed."

    car2 = create_dummy_car(Direction.EAST, x=-50)
    assert has_crossed_line(car2) is False, "East-bound car with x <= stop line should not be marked as having crossed."

def test_has_crossed_line_south():
    # For SOUTH, condition: car.y > stop line.
    car = create_dummy_car(Direction.SOUTH, y=-20)
    expected_line = get_stop_line(car)  # -37.5
    assert -20 > expected_line, "Test setup error: car.y should be greater than stop line."
    assert has_crossed_line(car) is True, "South-bound car with y > stop line should be marked as having crossed."

    car2 = create_dummy_car(Direction.SOUTH, y=-50)
    assert has_crossed_line(car2) is False, "South-bound car with y <= stop line should not be marked as having crossed."

def test_has_crossed_line_west():
    # For WEST, condition: car.x < stop line.
    car = create_dummy_car(Direction.WEST, x=130)
    expected_line = get_stop_line(car)  # 137.5
    assert 130 < expected_line, "Test setup error: car.x should be less than stop line."
    assert has_crossed_line(car) is True, "West-bound car with x < stop line should be marked as having crossed."

    car2 = create_dummy_car(Direction.WEST, x=150)
    assert has_crossed_line(car2) is False, "West-bound car with x >= stop line should not be marked as having crossed."

# -----------------------------------------------------------------------------
# Tests for queue_vehicle
# -----------------------------------------------------------------------------
def test_queue_vehicle_no_car_in_front():
    """
    If there is no car in front in the same lane and direction, the function should do nothing.
    """
    car = create_dummy_car(Direction.NORTH, y=150)
    all_cars = [car]
    queue_vehicle(car, all_cars)
    # Expect no change in position.
    assert car.y == 150, "Car position should remain unchanged when no vehicle is in front."

def test_queue_vehicle_north_adjustment():
    """
    For NORTH-bound vehicles, if the distance to the car in front is less than total_gap (height + 5),
    the car's y-coordinate should be adjusted.
    """
    # Car in front (lower y value) and car behind.
    car_front = create_dummy_car(Direction.NORTH, y=100, lane=0, height=10)
    car_behind = create_dummy_car(Direction.NORTH, y=110, lane=0, height=10)
    all_cars = [car_front, car_behind]
    total_gap = car_behind.height + 5  # 10+5 = 15
    # The current gap is 110 - 100 = 10, which is less than 15.
    queue_vehicle(car_behind, all_cars)
    # After adjustment, car_behind.y should be car_front.y + total_gap = 100 + 15 = 115.
    assert car_behind.y == 115, "North-bound car was not queued correctly."

def test_queue_vehicle_south_adjustment():
    """
    For SOUTH-bound vehicles, the car behind should be moved so that the gap equals (height + 5).
    """
    car_front = create_dummy_car(Direction.SOUTH, y=150, lane=0, height=10)
    car_behind = create_dummy_car(Direction.SOUTH, y=140, lane=0, height=10)
    all_cars = [car_front, car_behind]
    total_gap = car_behind.height + 5  # 15
    # Gap is 150 - 140 = 10, less than 15.
    queue_vehicle(car_behind, all_cars)
    # After adjustment, car_behind.y should be car_front.y - total_gap = 150 - 15 = 135.
    assert car_behind.y == 135, "South-bound car was not queued correctly."

def test_queue_vehicle_east_adjustment():
    """
    For EAST-bound vehicles, if the gap is less than total_gap, adjust the x-coordinate.
    """
    car_front = create_dummy_car(Direction.EAST, x=80, lane=0, height=10)
    car_behind = create_dummy_car(Direction.EAST, x=75, lane=0, height=10)
    all_cars = [car_front, car_behind]
    total_gap = car_behind.height + 5  # 15
    # Gap is 80 - 75 = 5, less than 15.
    queue_vehicle(car_behind, all_cars)
    # After adjustment, car_behind.x should be car_front.x - total_gap = 80 - 15 = 65.
    assert car_behind.x == 65, "East-bound car was not queued correctly."

def test_queue_vehicle_west_adjustment():
    """
    For WEST-bound vehicles, adjust the x-coordinate when gap is insufficient.
    """
    car_front = create_dummy_car(Direction.WEST, x=40, lane=0, height=10)
    car_behind = create_dummy_car(Direction.WEST, x=45, lane=0, height=10)
    all_cars = [car_front, car_behind]
    total_gap = car_behind.height + 5  # 15
    # Gap is 45 - 40 = 5, less than 15.
    queue_vehicle(car_behind, all_cars)
    # After adjustment, car_behind.x should be car_front.x + total_gap = 40 + 15 = 55.
    assert car_behind.x == 55, "West-bound car was not queued correctly."