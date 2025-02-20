from collections import deque
from simulation.enums import LaneType, Direction
from simulation.vehicle import Vehicle

class Lane:
    def __init__(self, lane_id: str, lane_type: LaneType, end: int):
        self.id = lane_id
        self.type = lane_type
        self.vehicles = deque()
        self.queueing_vehicles = deque()
        self.end = end # End of lane

    def is_position_occupied(self, position_x, position_y):
        # Check if a position is occupied by a vehicle.
        if not self.vehicles:
            return False
        vehicle = self.vehicles[-1]
        return vehicle.position_x == position_x and vehicle.position_y == position_y

    def move_vehicles(self):
        end_vehicle = None
        # Move vehicles forward
        for _ in range (len(self.vehicles)):
            vehicle = self.vehicles.popleft()
            vehicle.move()
            # Check if the new position is not occupied
            # while self.is_position_occupied(vehicle.position_x, vehicle.position_y) and (vehicle.position_x != old_x or vehicle.position_y != old_y):
            #     vehicle.moveBack()
            
            # Remove vehicles that have reached the end of the lane
            if self.has_reached_end(vehicle):
                end_vehicle = vehicle
            else:
                self.vehicles.append(vehicle)

        # Adds a queueing vehicle to lane if some are queuing
        if self.queueing_vehicles:
            self.vehicles.append(self.queueing_vehicles.popleft())

        return end_vehicle

    def has_reached_end(self, vehicle):
        # Check if vehicle has reached end of lane
        if (vehicle.direction == Direction.NORTH or vehicle.direction == Direction.SOUTH) and vehicle.position_y == self.end:
            return True
        elif (vehicle.direction == Direction.EAST or vehicle.direction == Direction.WEST) and vehicle.position_x == self.end:
            return True
        return False

    def add_vehicle(self, vehicle: Vehicle):
        # Adds a vehicle to the lane if starting position not occupied.
        if not self.is_position_occupied(vehicle.position_x, vehicle.position_y):
            self.vehicles.append(vehicle)
        else:
            self.queueing_vehicles.append(vehicle)
