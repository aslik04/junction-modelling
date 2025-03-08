"""
This module defines the Car class, which represents vehicles in the traffic simulation.
Each Car object has attributes such as direction, lane, speed, and turn type.
The class also determines the initial position and movement behavior of the car
within a simulated junction environment.
"""

import math
import random
from .enums import Direction, TurnType

class Car:
    """
    Represent the traffic inside of the simulation, it has attributes like direction, speed and lane
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
        Initializes a Car object with its movement attributes and position based on the junction data.
        
        Parameters:
            direction (Direction): The initial direction of the car (NORTH, EAST, SOUTH, WEST).
            lane (int): The lane in which the car is positioned (wot change from this).
            speed (float): The speed of the car (constant for all cars).
            turn_type (TurnType): The type of turn the car will take (LEFT, RIGHT, STRAIGHT).
            junctionData (dict): A dictionary containing junction configuration such as lane width, canvas dimensions, and lane numbers.
        
        Raises:
            ValueError: If the provided direction is invalid.
        """

        self.junctionData = junctionData

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
        Converts the Car object to a dictionary containg the attributes.
        
        Returns:
            dict: A dictionary containing the car's attributes such as direction, lane, speed, position, and dimensions.
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