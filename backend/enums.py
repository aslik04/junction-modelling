"""
This file is for defining enumerations for cardinal directions and types of turns vehicles can take.

The `Direction` enum represents the four cardinal directions (north, east, south, and west)
and is used throughout the simulation to avoid magic strings and typos.

The `TurnType` enum defines the possible movement types for a vehicle:
- FORWARD: go straight,
- LEFT: make a left turn,
- RIGHT: make a right turn.
"""

from enum import Enum

class Direction(str, Enum):
    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"

class TurnType(str, Enum):
    FORWARD = "forward"
    LEFT = "left"
    RIGHT = "right"