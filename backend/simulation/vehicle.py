"""

"""

import math
import random
from ..enums import Direction, TurnType

class Car:
    """
    
    """

    def __init__(
        self,
        direction: Direction,
        lane: int,
        speed: float,
        turn_type: TurnType,
        junctionData: dict
    ):
        """
        
        """

        self.inital_direction = direction
        self.direction = direction
        self.speed = speed
        self.turn_type = turn_type

        if turn_type == TurnType.LEFT:
            lane = 0
        elif turn_type == TurnType.RIGHT:
            lane = junctionData["numOfLanes"] - 1
        self.lane = lane

        self.width = junctionData["widthOfCar"] 
        self.height = junctionData["heightOfCar"]

        self.pngIndex = random.randint(0, 4)

        self.completedLeft = False

        self.rightTurnPhase = 0
        self.rightTurnInitialAngle = 0.0
        self.currentRightTurnAngle = 0.0
        
        self.passedStopLine = False

        if direction == Direction.NORTH:
            self.x = junctionData["leftVertical"] + junctionData["pixelWidthOfLane"] * (lane + 0.5)
            self.y = junctionData["canvasHeight"] + self.height
            self.rightTurnInitialAngle = 0.0

        elif direction == Direction.EAST:
            self.x = -self.width
            self.y = junctionData["topHorizontal"] + junctionData["pixelWidthOfLane"] * (lane + 0.5)
            self.rightTurnInitialAngle = math.pi / 2

        elif direction == Direction.SOUTH:
            self.x = junctionData["rightVertical"] - junctionData["pixelWidthOfLane"] * (lane + 0.5)
            self.y = -self.height
            self.rightTurnInitialAngle = math.pi

        elif direction == Direction.WEST:
            self.x = junctionData["canvasWidth"] + self.width
            self.y = junctionData["bottomHorizontal"] - junctionData["pixelWidthOfLane"] * (lane + 0.5)
            self.rightTurnInitialAngle = -math.pi / 2

        else:
            raise ValueError(f"Invalid direction: {direction}")

        self.currentRightTurnAngle = self.rightTurnInitialAngle

    def to_dict(self):
        """
        
        """

        return {
            "direction": self.direction,
            "lane": self.lane,
            "speed": self.speed,
            "turnType": self.turn_type,
            "x": self.x,
            "y": self.y,
            "currentRightTurnAngle": self.currentRightTurnAngle,
            "pngIndex": self.pngIndex, 
            "width": self.width,
            "height": self.height
        }