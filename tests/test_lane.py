import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from simulation.enums import Direction
from simulation.vehicle import Car
from simulation.lane import Lane

def test_vehicle_removal():
    lane = Lane("Lane1", None, end=5)
    car1 = Car("Car1", 0, 4, Direction.NORTH, Direction.NORTH)
    car2 = Car("Car2", 0, 2, Direction.NORTH, Direction.NORTH)

    lane.add_vehicle(car1)
    lane.add_vehicle(car2)

    removed_vehicle = lane.move_vehicles()

    assert removed_vehicle is car1
    assert len(lane.vehicles) == 1
    assert lane.vehicles[0] is car2
