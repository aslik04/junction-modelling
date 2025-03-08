"""
This module provides functions for controlling vehicle movement in the traffic simulation.
It includes functions for moving vehicles forward, executing left and right turns,
and handling vehicle updates based on traffic light signals and road conditions.
It also add new vehicles to the vehicle queue used in the simulation logic
"""

import math 
from .vehicle import Car
from .vehicle_stop_line import can_pass_stop_line, stop_at_stop_line, has_crossed_line, queue_vehicle
from .enums import Direction, TurnType

def move_forward(car: Car) -> None:
    """
    Moves the car forward in its current direction by its speed.
    
    Parameters:
        car (Car): The car to be moved.
    """

    if car.direction == Direction.NORTH:

        car.y -= car.speed
    elif car.direction == Direction.SOUTH:

        car.y += car.speed
    elif car.direction == Direction.EAST:

        car.x += car.speed
    elif car.direction == Direction.WEST:

        car.x -= car.speed

def move_left_turn(car: Car) -> None:
    """
    Handles a left turn for the car at an intersection, changing direction upon completion.
    
    Parameters:
        car (Car): The car executing the left turn.
    """

    junctionData = car.junctionData

    margin = 10  
    
    top = junctionData["topHorizontal"]
    bottom = junctionData["bottomHorizontal"]
    left = junctionData["leftVertical"]
    right = junctionData["rightVertical"]

    if not car.completedLeft:

        if car.direction == Direction.NORTH:

            if (car.y - car.speed) <= (bottom - margin):

                car.y = bottom - margin
                car.direction = Direction.WEST  # Consider using Direction.WEST if using enums consistently
                car.completedLeft = True
            else:

                car.y -= car.speed
        elif car.direction == Direction.EAST:

            if (car.x + car.speed) >= (left + margin):

                car.x = left + margin
                car.direction = Direction.NORTH
                car.completedLeft = True
            else:

                car.x += car.speed
        elif car.direction == Direction.SOUTH:

            if (car.y + car.speed) >= (top + margin):

                car.y = top + margin
                car.direction = Direction.EAST
                car.completedLeft = True
            else:

                car.y += car.speed
        elif car.direction == Direction.WEST:

            if (car.x - car.speed) <= (right - margin):

                car.x = right - margin
                car.direction = Direction.SOUTH
                car.completedLeft = True
            else:

                car.x -= car.speed
    else:
        move_forward(car)

def move_right_turn(car: Car) -> None:
    """
    Handles a right turn for the car using an incremental turn approach for smoother movement in the simulation.
    
    Parameters:
        car (Car): The car executing the right turn.
    """

    junctionData = car.junctionData

    margin = 15 

    top = junctionData["topHorizontal"]
    bottom = junctionData["bottomHorizontal"]
    left = junctionData["leftVertical"]
    right = junctionData["rightVertical"]

    car.x += car.speed * math.sin(car.currentRightTurnAngle)
    car.y += -car.speed * math.cos(car.currentRightTurnAngle)

    if car.rightTurnPhase == 0:

        if car.direction == Direction.NORTH and car.y <= bottom - margin:

            car.y = bottom - margin
            car.rightTurnPhase = 1
            car.currentRightTurnAngle += math.pi / 4
        elif car.direction == Direction.EAST and car.x >= left + margin:

            car.x = left + margin
            car.rightTurnPhase = 1
            car.currentRightTurnAngle += math.pi / 4
        elif car.direction == Direction.SOUTH and car.y >= top + margin:

            car.y = top + margin
            car.rightTurnPhase = 1
            car.currentRightTurnAngle += math.pi / 4
        elif car.direction == Direction.WEST and car.x <= right - margin:

            car.x = right - margin
            car.rightTurnPhase = 1
            car.currentRightTurnAngle += math.pi / 4

    elif car.rightTurnPhase == 1:

        if car.direction == Direction.NORTH and car.x >= right - margin:

            car.direction = Direction.EAST
            car.rightTurnPhase = 2
            car.currentRightTurnAngle += math.pi / 4

        elif car.direction == Direction.EAST and car.y >= bottom - margin:

            car.direction = Direction.SOUTH
            car.rightTurnPhase = 2
            car.currentRightTurnAngle += math.pi / 4

        elif car.direction == Direction.SOUTH and car.x <= left + margin:

            car.direction = Direction.WEST
            car.rightTurnPhase = 2
            car.currentRightTurnAngle += math.pi / 4

        elif car.direction == Direction.WEST and car.y <= top + margin:

            car.direction = Direction.NORTH
            car.rightTurnPhase = 2
            car.currentRightTurnAngle += math.pi / 4

    else:
        move_forward(car)

def update_vehicle(car: Car, traffic_lights: dict, right_turn_lights: dict, all_cars: list) -> None:
    """
    Updates the vehicle's movement based on traffic light signals and road conditions
    Ensures that vehicles stop at stop lines if necessary
    Adds the vehicle to the vehicle queue for simulation logic
    
    Parameters:
        car (Car): The car to update.
        traffic_lights (dict): Dictionary containing traffic light states.
        right_turn_lights (dict): Dictionary containing right turn signal states.
        all_cars (list): A list of all cars in the simulation.
    """

    if not car.passedStopLine:

        if car.turn_type in ["forward", "left"]:

            allowed = traffic_lights.get(car.direction, {}).get("green", False)

            if not allowed:

                if not can_pass_stop_line(car):

                    stop_at_stop_line(car)
                    queue_vehicle(car, all_cars)
                    return
        else:

            arrow_on = right_turn_lights.get(car.direction, {}).get("on", False)

            if not arrow_on:

                if not can_pass_stop_line(car):

                    stop_at_stop_line(car)
                    queue_vehicle(car, all_cars)
                    return

    if car.turn_type == TurnType.FORWARD:
        move_forward(car)

    elif car.turn_type == TurnType.LEFT:
        move_left_turn(car)

    else:
        move_right_turn(car)

    if has_crossed_line(car):
        car.passedStopLine = True

    queue_vehicle(car, all_cars)