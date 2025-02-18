from enum import Enum

class Direction(Enum):
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"

class LaneType(Enum):
    REGULAR = "REGULAR"
    BUS_LANE_CYCLE_LANE = "BUS_LANE/CYCLE_LANE"
    LEFT_TURN_LANE = "LEFT_TURN_LANE"

class LightState(Enum):
    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"
