import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
#import pytest
from backend.junction_objects.vehicle_movement import (
    move_forward,
    move_left_turn,
    move_right_turn,
    update_vehicle,
)
from backend.junction_objects.enums import Direction, TurnType

# -----------------------------------------------------------------------------
# Helper: A simple dummy car for our tests.
# -----------------------------------------------------------------------------
class DummyCar:
    pass

def create_dummy_car(direction, turn_type, speed=10):
    """
    Create a dummy car with the attributes needed for the movement tests.
    The junctionData dictionary is populated with sample values.
    """
    car = DummyCar()
    car.direction = direction
    car.turn_type = turn_type
    car.speed = speed
    car.x = 50
    car.y = 50
    car.junctionData = {
        "topHorizontal": 0,
        "bottomHorizontal": 100,
        "leftVertical": 0,
        "rightVertical": 100,
        "canvasHeight": 200,
        "canvasWidth": 200,
        "pixelWidthOfLane": 10,
        "widthOfCar": 5,
        "heightOfCar": 10,
        "numOfLanes": 3
    }
    car.completedLeft = False
    car.rightTurnPhase = 0
    car.rightTurnInitialAngle = 0.0
    car.currentRightTurnAngle = 0.0
    car.passedStopLine = False
    return car

# -----------------------------------------------------------------------------
# Tests for basic movement functions
# -----------------------------------------------------------------------------
def test_move_forward_north():
    car = create_dummy_car(Direction.NORTH, TurnType.FORWARD, speed=10)
    initial_y = car.y
    move_forward(car)
    assert car.y == initial_y - 10, "Moving NORTH should decrease the y-coordinate by speed."

def test_move_forward_south():
    car = create_dummy_car(Direction.SOUTH, TurnType.FORWARD, speed=10)
    initial_y = car.y
    move_forward(car)
    assert car.y == initial_y + 10, "Moving SOUTH should increase the y-coordinate by speed."

def test_move_forward_east():
    car = create_dummy_car(Direction.EAST, TurnType.FORWARD, speed=10)
    initial_x = car.x
    move_forward(car)
    assert car.x == initial_x + 10, "Moving EAST should increase the x-coordinate by speed."

def test_move_forward_west():
    car = create_dummy_car(Direction.WEST, TurnType.FORWARD, speed=10)
    initial_x = car.x
    move_forward(car)
    assert car.x == initial_x - 10, "Moving WEST should decrease the x-coordinate by speed."

def test_move_left_turn_trigger():
    """
    For a left turn, if the car is near the turning margin, it should set its position
    to the boundary (bottom - margin for NORTH), change direction, and mark the turn as completed.
    """
    # For a car coming from NORTH, margin is 10 and bottom = 100.
    # Condition triggers if (y - speed) <= (bottom - margin), i.e. if y <= 100.
    car = create_dummy_car(Direction.NORTH, TurnType.LEFT, speed=10)
    car.y = 95  # 95 - 10 = 85, which is <= (100 - 10 = 90)
    move_left_turn(car)
    assert car.y == 90, "After turning, car.y should be set to bottom - margin (90)."
    assert car.direction == Direction.WEST, "After a left turn from NORTH, direction should change to WEST."
    assert car.completedLeft is True, "Car should be marked as having completed its left turn."

def test_move_left_turn_non_trigger():
    """
    When the car is far from the turning boundary, it should simply move forward.
    """
    car = create_dummy_car(Direction.NORTH, TurnType.LEFT, speed=10)
    car.y = 150  # 150 - 10 = 140, which is > (100 - 10 = 90)
    move_left_turn(car)
    assert car.y == 140, "Car should simply move forward if the left-turn condition is not met."
    assert car.completedLeft is False, "Car should not mark left turn as completed if condition is not met."

def test_move_left_turn_after_completed():
    """
    Once a left turn has been completed, subsequent calls should just move the car forward.
    """
    car = create_dummy_car(Direction.NORTH, TurnType.LEFT, speed=10)
    car.completedLeft = True
    initial_y = car.y
    move_left_turn(car)
    assert car.y == initial_y - 10, "After a left turn is completed, move_left_turn should behave like move_forward."

def test_move_right_turn_trigger_phase_0():
    """
    For a right turn, in phase 0 the car moves until it reaches a margin.
    For a NORTH-bound car, when (y - speed) puts it below (bottom - margin),
    the car should snap to (bottom - margin), switch to phase 1, and increment its turn angle.
    """
    car = create_dummy_car(Direction.NORTH, TurnType.RIGHT, speed=10)
    # Set up: bottom = 100 and margin = 15, so threshold is 85.
    car.y = 90  # With speed 10, new y would be 80 which is <= 85.
    initial_angle = car.currentRightTurnAngle
    move_right_turn(car)
    assert car.y == 85, "In phase 0, car.y should be set to bottom - margin (85) when condition is met."
    assert car.rightTurnPhase == 1, "Right turn phase should change to 1 after the phase 0 trigger."
    expected_angle = initial_angle + math.pi / 4
    assert math.isclose(car.currentRightTurnAngle, expected_angle, rel_tol=1e-5), "Right turn angle should increase by pi/4."

def test_move_right_turn_phase_1_trigger():
    """
    For phase 1 of a right turn, when the car meets the condition,
    its direction should change (e.g. from NORTH to EAST), phase updated, and turn angle incremented.
    """
    car = create_dummy_car(Direction.NORTH, TurnType.RIGHT, speed=10)
    car.rightTurnPhase = 1
    car.currentRightTurnAngle = 0.0
    # For a NORTH-bound car in phase 1, if x >= (right - margin), with right = 100 and margin = 15,
    # then condition is met if x >= 85.
    car.x = 90
    move_right_turn(car)
    assert car.direction == Direction.EAST, "In phase 1, NORTH-bound car should change direction to EAST."
    assert car.rightTurnPhase == 2, "Right turn phase should update to 2 after phase 1 trigger."
    assert math.isclose(car.currentRightTurnAngle, math.pi / 4, rel_tol=1e-5), "Turn angle should increase by pi/4 in phase 1."

# -----------------------------------------------------------------------------
# Tests for update_vehicle function
# -----------------------------------------------------------------------------
def test_update_vehicle_forward_green(monkeypatch):
    """
    When the light is green for a forward-moving vehicle, update_vehicle should allow movement.
    We simulate a green light and override stop-line functions to return favorable conditions.
    """
    car = create_dummy_car(Direction.NORTH, TurnType.FORWARD, speed=10)
    original_y = car.y

    # Create dummy traffic light dictionaries.
    traffic_lights = { car.direction: {"green": True} }
    right_turn_lights = {}  # not used for forward movement.
    all_cars = []

    # Define dummy stop-line functions.
    def dummy_can_pass(car):
        return True
    def dummy_stop_at(car):
        car.stopped = True  # mark the car if called.
    def dummy_has_crossed(car):
        return True
    def dummy_queue(car, lst):
        lst.append(car)

    # Patch the functions in the globals of update_vehicle.
    monkeypatch.setitem(update_vehicle.__globals__, "can_pass_stop_line", dummy_can_pass)
    monkeypatch.setitem(update_vehicle.__globals__, "stop_at_stop_line", dummy_stop_at)
    monkeypatch.setitem(update_vehicle.__globals__, "has_crossed_line", dummy_has_crossed)
    monkeypatch.setitem(update_vehicle.__globals__, "queue_vehicle", dummy_queue)

    update_vehicle(car, traffic_lights, right_turn_lights, all_cars)
    # For a NORTH-bound car, move_forward should decrease y.
    assert car.y == original_y - 10, "With green light, car should move forward."
    # Since dummy has_crossed returns True, passedStopLine should be set.
    assert car.passedStopLine is True, "Car passedStopLine should be True after moving if line is crossed."
    # And the car should have been added to the vehicle queue.
    assert car in all_cars, "Car should be queued after update_vehicle."

def test_update_vehicle_stop(monkeypatch):
    """
    If the light is not green (or arrow not on for right-turn) and the car cannot pass the stop line,
    update_vehicle should call stop_at_stop_line and queue the vehicle without moving it.
    """
    car = create_dummy_car(Direction.NORTH, TurnType.FORWARD, speed=10)
    original_x, original_y = car.x, car.y

    traffic_lights = { car.direction: {"green": False} }
    right_turn_lights = {}
    all_cars = []
    stop_called = False
    def dummy_can_pass(car):
        return False
    def dummy_stop_at(car):
        nonlocal stop_called
        stop_called = True
    def dummy_queue(car, lst):
        lst.append(car)
    monkeypatch.setitem(update_vehicle.__globals__, "can_pass_stop_line", dummy_can_pass)
    monkeypatch.setitem(update_vehicle.__globals__, "stop_at_stop_line", dummy_stop_at)
    monkeypatch.setitem(update_vehicle.__globals__, "queue_vehicle", dummy_queue)
    monkeypatch.setitem(update_vehicle.__globals__, "has_crossed_line", lambda car: False)

    update_vehicle(car, traffic_lights, right_turn_lights, all_cars)
    # Expect no movement because the vehicle should stop.
    assert car.x == original_x and car.y == original_y, "Car should not move when it cannot pass the stop line."
    assert stop_called, "stop_at_stop_line should be called when vehicle cannot pass."
    assert car in all_cars, "Car should be queued even when stopped."

def test_update_vehicle_right(monkeypatch):
    """
    For a right-turning vehicle, if the right-turn signal is on,
    update_vehicle should perform a right turn (i.e. move the car) and update passedStopLine.
    """
    car = create_dummy_car(Direction.NORTH, TurnType.RIGHT, speed=10)
    original_x, original_y = car.x, car.y

    traffic_lights = {}  # not used for right-turn.
    right_turn_lights = { car.direction: {"on": True} }
    all_cars = []
    monkeypatch.setitem(update_vehicle.__globals__, "can_pass_stop_line", lambda car: True)
    monkeypatch.setitem(update_vehicle.__globals__, "stop_at_stop_line", lambda car: None)
    monkeypatch.setitem(update_vehicle.__globals__, "has_crossed_line", lambda car: True)
    monkeypatch.setitem(update_vehicle.__globals__, "queue_vehicle", lambda car, lst: lst.append(car))

    update_vehicle(car, traffic_lights, right_turn_lights, all_cars)
    # We don't check an exact coordinate change (due to trigonometry),
    # but we expect the position to change from its original.
    moved = (car.x != original_x) or (car.y != original_y)
    assert moved, "Car should move during a right turn."
    assert car.passedStopLine is True, "Car should be marked as having passed the stop line after moving."
    assert car in all_cars, "Car should be queued after update_vehicle for a right turn."