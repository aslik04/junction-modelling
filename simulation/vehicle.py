from abc import ABC, abstractmethod
from simulation.enums import Direction

class Vehicle(ABC):
    def __init__(self, vehicle_id: str, position_x: int, position_y: int, direction: Direction, destination: Direction):
        self.id = vehicle_id
        self.position_x = position_x
        self.position_y = position_y
        self.direction = direction
        self.destination = destination

    @abstractmethod
    def move(self): # Defines how vehicles move
        pass

    def moveBack(self): # Moves back by 1
        if self.direction == Direction.NORTH:
            self.position_y -= 1
        elif self.direction == Direction.SOUTH:
            self.position_y += 1
        elif self.direction == Direction.EAST:
            self.position_x -= 1
        elif self.direction == Direction.WEST:
            self.position_x += 1

class Car(Vehicle):
    def move(self):
        # Movement for car
        if self.direction == Direction.NORTH:
            self.position_y += 1
        elif self.direction == Direction.SOUTH:
            self.position_y -= 1
        elif self.direction == Direction.EAST:
            self.position_x += 1
        elif self.direction == Direction.WEST:
            self.position_x -= 1
    def moveBack(self):
        return super().move_back()

class Bus(Vehicle):
    def move(self):
        # Movement for Bus
        if self.direction == Direction.NORTH:
            self.position_y += 1
        elif self.direction == Direction.SOUTH:
            self.position_y -= 1
        elif self.direction == Direction.EAST:
            self.position_x += 1
        elif self.direction == Direction.WEST:
            self.position_x -= 1
    def moveBack(self):
        return super().move_back()

class Bicycle(Vehicle):
    def move(self):
        # Movement for Bicycle
        if self.direction == Direction.NORTH:
            self.position_y += 1  # TODO: Smaller movement for Bicycles?
        elif self.direction == Direction.SOUTH:
            self.position_y -= 1
        elif self.direction == Direction.EAST:
            self.position_x += 1
        elif self.direction == Direction.WEST:
            self.position_x -= 1
    def moveBack(self):
        return super().move_back()