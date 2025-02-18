from collections import deque
from simulation.enums import LaneType, Direction
from simulation.vehicle import Vehicle

class Lane:
    def __init__(self, lane_id: str, lane_type: LaneType, length: int = 100):
        self.id = lane_id
        self.type = lane_type
        self.vehicles = deque()
        self.length = length  # Length of lane

    def is_position_occupied(self, position_x, position_y):
        # Check if a position is occupied by a vehicle.
        return any(vehicle.position_x == position_x and vehicle.position_y == position_y for vehicle in self.vehicles)

    def move_vehicles(self):
        # Move vehicles forward
        vehicles = self.vehicles
        self.vehicles = deque()
        for vehicle in list(vehicles):
            old_x = vehicle.position_x
            old_y = vehicle.position_y
            vehicle.move()

            # Check if the new position is not occupied
            while self.is_position_occupied(vehicle.position_x, vehicle.position_y) and (vehicle.position_x != old_x or vehicle.position_y != old_y):
                vehicle.moveBack()
            self.vehicles.append(vehicle)

        # Remove vehicles that have reached the end of the lane
        self.vehicles = deque([v for v in self.vehicles if not self.has_reached_end(v)])

    def has_reached_end(self, vehicle):
        # Check if vehicle has reached end of lane
        if vehicle.direction == Direction.NORTH and vehicle.position_y >= self.length:
            return True
        if vehicle.direction == Direction.SOUTH and vehicle.position_y <= 0:
            return True
        if vehicle.direction == Direction.EAST and vehicle.position_x >= self.length:
            return True
        if vehicle.direction == Direction.WEST and vehicle.position_x <= 0:
            return True
        return False

    def add_vehicle(self, vehicle: Vehicle):
        # Adds a vehicle to the lane if starting position not occupied.
        if not self.is_position_occupied(vehicle.position_x, vehicle.position_y):
            self.vehicles.append(vehicle)
