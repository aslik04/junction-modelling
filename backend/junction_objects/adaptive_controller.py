"""
This file implements an adaptive traffic light algorithm that dynamically adjusts the duration,
of green lights based on real-time traffic conditions. 
The goal is to minimise waiting times and queue lengths while safely accomodating pedestrian events.

Overview:
Traffic signals are controlled using a **nonlinear green duration calculation** that adjusts based on queue lengths. 
Exponential smoothing is applied to ensure gradual transitions between different light durations, preventing sudden changes.

This algorithm operates in a continuous **adaptive control loop** that alternates between vertical (North-South) 
and horizontal (East-West) traffic flows, dynamically adjusting green light durations based on detected queue lengths. 
It also incorporates pedestrian crossings at randomized intervals, based on user inputs.

Key Features:
1. Real-Time Queue Detection: 
   - The system counts vehicles waiting for corresponding lights, where the main lights are for left and forward, 
     and right turn lights is for right turns only, so we constantly calculate the wait counts for these lights. 
   - These are done for Vertical (North and South) and for Horizontal (East and West), simply for logical reasons
     as for optimal efficiency and safety these should be treated together due to being able to not drive in each others way.

2. Nonlinear Green Duration Calculation:
   - Uses the formula: Green duration = (min + (max - min) * queue length) / (queue length + k)
   - Key Parameters:
     - `min`: Minimum allowed green duration, set to 2.
     - `max`: Maximum allowed green duration, set to 20.
     - `k`: A nonlinear factor that determines the responsiveness of the green duration to queue length.
       - Smaller `k` → Green time increases quickly overtime, even with few cars.
       - Larger `k` → Requires longer queues before significantly increasing green time overtime.

3. Exponential Smoothing for Gradual Changes:
   - Sudden changes in green duration are prevented using exponential smoothing:
     Smooth Duration = ((1 - alpha) * previous duration) + (alpha * desired duration)
   - Alpha Parameter Behavior:
     - `0.0` → No immediate change, green time is fully stable.
     - `1.0` → Instantaneous change, no smoothing applied.
     - Recommended Range to Utilise: `0.1 - 0.3` for balancing responsiveness and stability.

5. Pedestrian Crossing Events:
   - Pedestrian events are randomly triggered based on a user set frequency.
   - During pedestrian crossings:
     - All vehicle signals turn red.
     - Pedestrian signals turn on for duration set by user.
   - Once the pedestrian phase ends, the system resumes normal traffic flow.

6. Adaptive Control Loop:
   - The loop continuously:
     1. Calculates the green duration for both vertical and horizontal traffic.
     2. Smooths the transition between changes.
     3. Alternates traffic phases based on calculated durations.
     4. Handles right-turn phases when required.
     5. Randomly initiates pedestrian crossings at configured intervals.

Dependencies:
- `asyncio`: Used for handling non-blocking sleep calls and state changes.
- `random`: Used for probabilistic pedestrian event triggering.
"""


import asyncio
import random

def get_vertical_wait_count(cars: list) -> int:
    """
    Count the number of waiting vehicles traveling vertically (north/south bound)
    that haven't passed the stop line and aren't turning right,
    and have not passed the stop line therefore havent entered the junction.

    Parameters:
        cars: List of vehicle objects with direction and state information

    Returns:
        int: Count of waiting vertical-traveling vehicles
    """

    return sum(1 for car in cars if car.inital_direction in ("north", "south") 
               and not car.passedStopLine and car.turn_type != "right")

def get_horizontal_wait_count(cars: list) -> int:
    """
    Count the number of waiting vehicles traveling horizontally (east/west bound)
    that haven't passed the stop line and aren't turning right, 
    and have not passed the stop line therefore havent entered the junction.

    Parameters:
        cars: List of vehicle objects with direction and state information
        
    Returns:
        int: Count of waiting horizontal-traveling vehicles
    """

    return sum(1 for car in cars if car.inital_direction in ("east", "west") 
               and not car.passedStopLine and car.turn_type != "right")

def get_vertical_right_wait_count(cars: list) -> int:
    """
    Count the number of waiting vehicles traveling vertically (north/south bound)
    that are turning right and haven't passed the stop line, 
    and thus have not entered the junction.
    
    Parameters:
        cars: List of vehicle objects with direction and state information
        
    Returns:
        int: Count of waiting right-turning vertical vehicles
    """

    return sum(1 for car in cars if car.inital_direction in ("north", "south") 
               and car.turn_type == "right" and not car.passedStopLine)

def get_horizontal_right_wait_count(cars: list) -> int:
    """
    Count the number of waiting vehicles traveling horizontally (east/west bound)
    that are turning right and haven't passed the stop line,
    and thus have not entered the junction.

    Parameters:
        cars: List of vehicle objects with direction and state information
        
    Returns:
        int: Count of waiting right-turning horizontal vehicles
    """

    return sum(1 for car in cars if car.inital_direction in ("east", "west") 
               and car.turn_type == "right" and not car.passedStopLine)

def nonlinear_green(count: int, min_green: float, max_green: float, k: float = 2.0) -> float:
    """
    Calculate green light duration using a nonlinear function of queue length.
    Duration increases with queue length but plateaus at max_green.

    Parameters:
        count: Number of waiting vehicles
        min_green: Minimum green light duration
        max_green: Maximum green light duration 
        k: Curve steepness parameter (default 2.0)

    Returns:
        float: Calculated green light duration in seconds
    """

    return min_green + (max_green - min_green) * (count / (count + k))

async def set_phase(controller, phase: str) -> None:
    """
    Sets the traffic light phase for the junction controller.
    This function updates the traffic light states based on the specified phase:
    - 'vertical': Sets north-south traffic flows to green and east-west to red
    - 'horizontal': Sets east-west traffic flows to green and north-south to red  
    - 'red': Sets all traffic lights to red

    Parameters:
        controller: The junction controller object containing traffic light states
        phase (str): The desired phase - either "vertical", "horizontal" or "red"

    Returns:
        None: Updates controller state and broadcasts it asynchronously
    """

    if phase == "vertical":

        controller.trafficLightStates["north"] = {"red": False, "amber": False, "green": True}
        controller.trafficLightStates["south"] = {"red": False, "amber": False, "green": True}
        controller.trafficLightStates["east"] = {"red": True, "amber": False, "green": False}
        controller.trafficLightStates["west"] = {"red": True, "amber": False, "green": False}
    
    elif phase == "horizontal":
    
        controller.trafficLightStates["east"] = {"red": False, "amber": False, "green": True}
        controller.trafficLightStates["west"] = {"red": False, "amber": False, "green": True}
        controller.trafficLightStates["north"] = {"red": True, "amber": False, "green": False}
        controller.trafficLightStates["south"] = {"red": True, "amber": False, "green": False}
    
    elif phase == "red":
    
        for d in ["north", "east", "south", "west"]:
            controller.trafficLightStates[d] = {"red": True, "amber": False, "green": False}
    
    await controller._broadcast_state()

async def run_right_turn_phase(controller, directions: list, phase_time: float, sim_speed: float, transition_time: float) -> None:
    """
    Executes a right turn signal phase for specified directions in the traffic controller.
    This function sets the right turn signals to green for the given directions, maintains this state
    for the specified phase duration, then turns them off and waits for a transition period.
    
    Parameters:
        controller: The traffic controller instance managing the junction
        directions (list): List of directions where right turn signals should be activated
        phase_time (float): Duration in seconds for which the right turn signals stay green
        sim_speed (float): Simulation speed multiplier (e.g., 2.0 means simulation runs twice as fast)
        transition_time (float): Duration in seconds for the transition period after signals turn off
    
    Note:
        This is an asynchronous function that uses asyncio.sleep() for timing control
        The actual duration of phases will be divided by sim_speed to account for simulation speed
    """
    
    for d in directions:
        controller.rightTurnLightStates[d] = {"off": False, "on": True}
    
    await controller._broadcast_state()
    
    await asyncio.sleep(phase_time / sim_speed)
    
    for d in directions:
        controller.rightTurnLightStates[d] = {"off": True, "on": False}
    await controller._broadcast_state()
    
    await asyncio.sleep(transition_time / sim_speed)

async def run_pedestrian_event(controller) -> None:
    """
    Executes a pedestrian crossing event in all directions of the junction.
    This asynchronous function performs the following sequence:
    1. Turns all traffic lights red and turns off right turn signals
    2. Activates pedestrian crossing lights in all directions
    3. Maintains pedestrian crossing state for the configured duration
    4. Deactivates pedestrian crossing lights
    
    Parameters:
        controller: The junction controller instance containing the traffic light states
                    and timing configurations

    Note:
        The function uses the controller's simulationSpeedMultiplier to adjust timing
        of state changes and pedestrian crossing duration
    """
    
    for d in ["north", "east", "south", "west"]:
        
        controller.trafficLightStates[d] = {"red": True, "amber": False, "green": False}
        controller.rightTurnLightStates[d] = {"off": True, "on": False}
        
        await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)
        
        controller.pedestrianLightStates[d] = {"off": False, "on": True}
    
    await controller._broadcast_state()
    
    await asyncio.sleep(controller.pedestrianDuration / controller.simulationSpeedMultiplier)
    
    for d in ["north", "east", "south", "west"]:
        controller.pedestrianLightStates[d] = {"off": True, "on": False}
    
    await controller._broadcast_state()

async def run_adaptive_traffic_loop(controller, cars: list, gap: float = 0.005) -> None:
    """
    Executes the main adaptive traffic control loop for managing traffic flow at an intersection.
    This function implements an adaptive traffic control system that dynamically adjusts signal
    timing based on real-time traffic conditions. The system operates through the following
    key mechanisms:
    
    Signal Timing:
    - Monitors vehicle queues in both vertical (north-south) and horizontal (east-west) directions
    - Calculates optimal green light duration using a nonlinear function (min: 2s, max: 20s)
    - Applies exponential smoothing to prevent abrupt timing changes
    - Maintains minimum transition times between phase changes
    
    Right Turn Management:
    - Processes dedicated right turn phases for both vertical and horizontal approaches
    - Activates when vehicles are queued for right turns
    
    Pedestrian Crossing System:
    - Implements probabilistic pedestrian event generation
    - Maintains target pedestrian events per minute based on controller settings
    - Dynamically adjusts event probability based on remaining time and target events
    - Ensures uniform distribution of pedestrian crossings throughout each minute
    
    Parameters:
        controller: Traffic light controller instance managing the intersection
        cars (list): Current vehicles in the simulation
        gap (float, optional): Base time interval between state changes. Defaults to 0.005
    
    The function runs indefinitely, continuously adapting to changing traffic patterns and
    maintaining smooth traffic flow while accommodating both vehicular and pedestrian traffic.
    """
    
    min_green = 2
    max_green = 20
    k = 2.0
    transition_time = gap_time = gap
    smoothing_alpha = 0.1
    smoothed_vertical = min_green
    smoothed_horizontal = min_green
    smoothed_vertical_right = min_green
    smoothed_horizontal_right = min_green
    loop = asyncio.get_event_loop()

    print(controller.pedestrianPerMinute)
    print(controller.pedestrianDuration)
    
    while True:
        sim_speed = controller.simulationSpeedMultiplier
        vertical_count = get_vertical_wait_count(cars)
        horizontal_count = get_horizontal_wait_count(cars)
        vertical_right_count = get_vertical_right_wait_count(cars)
        horizontal_right_count = get_horizontal_right_wait_count(cars)
        desired_vertical = nonlinear_green(vertical_count, min_green, max_green, k) if vertical_count > 0 else 0
        desired_horizontal = nonlinear_green(horizontal_count, min_green, max_green, k) if horizontal_count > 0 else 0
        smoothed_vertical = (1 - smoothing_alpha) * smoothed_vertical + smoothing_alpha * desired_vertical
        smoothed_horizontal = (1 - smoothing_alpha) * smoothed_horizontal + smoothing_alpha * desired_horizontal
        desired_vertical_right = nonlinear_green(vertical_right_count, min_green, max_green, k) if vertical_right_count > 0 else 0
        desired_horizontal_right = nonlinear_green(horizontal_right_count, min_green, max_green, k) if horizontal_right_count > 0 else 0
        smoothed_vertical_right = (1 - smoothing_alpha) * smoothed_vertical_right + smoothing_alpha * desired_vertical_right  
        smoothed_horizontal_right = (1 - smoothing_alpha) * smoothed_horizontal_right + smoothing_alpha * desired_horizontal_right
        
        if smoothed_vertical > 0:
        
            await set_phase(controller, "vertical")
            await asyncio.sleep(smoothed_vertical / sim_speed)
            await set_phase(controller, "red")
            await asyncio.sleep(transition_time / sim_speed)
        
        else:
        
            await set_phase(controller, "red")
            await asyncio.sleep(gap_time / sim_speed)
        
        if vertical_right_count > 0:
        
            await run_right_turn_phase(controller, ["north", "south"], smoothed_vertical_right, sim_speed, transition_time)
        
        else:
        
            await asyncio.sleep(gap_time / sim_speed)
        
        if smoothed_horizontal > 0:
        
            await set_phase(controller, "horizontal")
            await asyncio.sleep(smoothed_horizontal / sim_speed)
            await set_phase(controller, "red")
            await asyncio.sleep(transition_time / sim_speed)
        
        else:
        
            await set_phase(controller, "red")
            await asyncio.sleep(gap_time / sim_speed)
        
        if horizontal_right_count > 0:
        
            await run_right_turn_phase(controller, ["east", "west"], smoothed_horizontal_right, sim_speed, transition_time)
        
        else:
        
            await asyncio.sleep(gap_time / sim_speed)
        
        p_gap = controller.pedestrianPerMinute / 10.0

        p_gap = min(p_gap, 1.0)
        
        if random.random() < p_gap:
            await run_pedestrian_event(controller)

        
        await asyncio.sleep(gap_time / sim_speed)