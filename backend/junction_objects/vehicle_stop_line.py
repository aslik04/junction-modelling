"""

"""

from .vehicle import Car 
from .enums import Direction

def get_stop_line(car: Car) -> float:
    """
    
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