"""
This module contains utility functions for managing car behavior at intersections.
It provides functions to determine stop lines, check if a car can pass or has crossed a stop line,
stop a car at the stop line, and manage vehicle queuing to maintain proper spacing.
"""

from .vehicle import Car 
from .enums import Direction

def get_stop_line(car: Car) -> float:
    """
    Determines the stop line position for a given car based on its direction 
    along with a width of the stop line.
    
    Args:
        car (Car): The car for which to calculate the stop line position.
    
    Returns:
        float: The stop line position along the corresponding axis.
    """


    junctionData = car.junctionData

    pw = junctionData["pixelWidthOfLane"]

    offset = pw * 1.25 + 25

    if car.direction == Direction.NORTH:

        return junctionData["bottomHorizontal"] + offset
    elif car.direction == Direction.EAST:

        return junctionData["leftVertical"] - offset
    elif car.direction == Direction.SOUTH:

        return junctionData["topHorizontal"] - offset
    elif car.direction == Direction.WEST:

        return junctionData["rightVertical"] + offset
    
    return 0

def can_pass_stop_line(car: Car) -> bool:
    """
    Checks if a car can pass the stop line based on its direction and speed.
    
    Args:
        car (Car): The car to check.
    
    Returns:
        bool: True if the car can pass the stop line, False otherwise.
    """

    line = get_stop_line(car)

    if car.direction == Direction.NORTH:

        return (car.y - car.speed) >= line
    elif car.direction == Direction.EAST:

        return (car.x + car.speed) <= line
    elif car.direction == Direction.SOUTH:

        return (car.y + car.speed) <= line
    elif car.direction == Direction.WEST:

        return (car.x - car.speed) >= line
    
    return True

def stop_at_stop_line(car: Car) -> None:
    """
    Adjusts a car's position to stop at the stop line on the simulation.
    
    Args:
        car (Car): The car to adjust.
    """

    line = get_stop_line(car)

    if car.direction == Direction.NORTH:
        car.y = line
    elif car.direction == Direction.EAST:
        car.x = line
    elif car.direction == Direction.SOUTH:
        car.y = line
    elif car.direction == Direction.WEST:
        car.x = line

def has_crossed_line(car: Car) -> bool:
    """
    Determines whether a car has crossed the stop line.
    
    Args:
        car (Car): The car to check.
    
    Returns:
        bool: True if the car has crossed the stop line, False otherwise.
    """

    line = get_stop_line(car)

    if car.direction == Direction.NORTH:

        return car.y < line
    elif car.direction == Direction.EAST:

        return car.x > line
    elif car.direction == Direction.SOUTH:

        return car.y > line
    elif car.direction == Direction.WEST:

        return car.x < line
    
    return False

def queue_vehicle(car: Car, all_cars: list) -> None:
    """
    Manages vehicle queuing by ensuring a car maintains proper distance
    (same distance for all vehicles)from the vehicle ahead.
    
    Args:
        car (Car): The car to be queued.
        all_cars (list): A list of all cars in the simulation.
    """

    total_gap = car.height + 5

    car_in_front = None

    for other in all_cars:

        if other is car:
            continue

        if other.direction == car.direction and other.lane == car.lane:

            if car.direction == Direction.NORTH:
                
                if other.y < car.y and (car_in_front is None or other.y > car_in_front.y):

                    car_in_front = other
            elif car.direction == Direction.SOUTH:

                if other.y > car.y and (car_in_front is None or other.y < car_in_front.y):
                    
                    car_in_front = other
            elif car.direction == Direction.EAST:

                if other.x > car.x and (car_in_front is None or other.x < car_in_front.x):
                    
                    car_in_front = other
            elif car.direction == Direction.WEST:

                if other.x < car.x and (car_in_front is None or other.x > car_in_front.x):
                    
                    car_in_front = other

    if car_in_front is None:
        return

    if car.direction == Direction.NORTH:

        dist = car.y - car_in_front.y

        if dist < total_gap:

            car.y = car_in_front.y + total_gap
    elif car.direction == Direction.SOUTH:

        dist = car_in_front.y - car.y

        if dist < total_gap:

            car.y = car_in_front.y - total_gap
    elif car.direction == Direction.EAST:

        dist = car_in_front.x - car.x

        if dist < total_gap:

            car.x = car_in_front.x - total_gap
    elif car.direction == Direction.WEST:

        dist = car.x - car_in_front.x
        
        if dist < total_gap:
            car.x = car_in_front.x + total_gap