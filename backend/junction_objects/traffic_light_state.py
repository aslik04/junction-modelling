"""
Traffic Light State Controller File

This file implements the traffic light state management and sequence control for a 4-way intersection.
It handles:
- Vertical (North-South) traffic sequences
- Horizontal (East-West) traffic sequences  
- Pedestrian crossing events
- Right turn signal coordination
- Timing and synchronization of light changes
- Probabilistic pedestrian event generation
- Running traffic configurations chosen by client

The file uses asyncio for asynchronous execution and timing control, with configurable 
simulation speed multipliers for testing. Traffic light states are managed through a 
TrafficLightController class that broadcasts state changes to connected clients.
"""

import asyncio
import random
from .traffic_light_controller import TrafficLightController
from .enums import Direction, TrafficLightSignal

async def run_vertical_sequence(controller: TrafficLightController) -> None:
    """
    Executes a traffic light sequence for vertical (North-South) traffic flow.
    
    This function controls the traffic light states for North-South directions, including:
    1. Waiting for East-West right turns to complete
    2. Running main traffic light sequence (Red -> Red+Amber -> Green -> Amber -> Red)
    3. Activating right turn signals for North-South traffic

    Use of simulationSpeedMultiplier, in order to speed up simulation synchronously.
    
    Parameters:
        controller: TrafficLightController instance managing the traffic states
    """

    while (controller.rightTurnLightStates[Direction.EAST.value][TrafficLightSignal.ON.value] or 
           controller.rightTurnLightStates[Direction.WEST.value][TrafficLightSignal.ON.value]):
        
        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
    
    if controller.VERTICAL_SEQUENCE_LENGTH != 0:

        controller.trafficLightStates[Direction.NORTH.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        controller.trafficLightStates[Direction.SOUTH.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
        
        controller.trafficLightStates[Direction.NORTH.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: True,
            TrafficLightSignal.GREEN.value: False
        }

        controller.trafficLightStates[Direction.SOUTH.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: True,
            TrafficLightSignal.GREEN.value: False
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
        
        controller.trafficLightStates[Direction.NORTH.value] = {
            TrafficLightSignal.RED.value: False,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: True
        }

        controller.trafficLightStates[Direction.SOUTH.value] = {
            TrafficLightSignal.RED.value: False,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: True
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.VERTICAL_SEQUENCE_LENGTH / controller.simulationSpeedMultiplier)
        
        controller.trafficLightStates[Direction.NORTH.value] = {
            TrafficLightSignal.RED.value: False,
            TrafficLightSignal.AMBER.value: True,
            TrafficLightSignal.GREEN.value: False
        }

        controller.trafficLightStates[Direction.SOUTH.value] = {
            TrafficLightSignal.RED.value: False,
            TrafficLightSignal.AMBER.value: True,
            TrafficLightSignal.GREEN.value: False
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
        
        controller.trafficLightStates[Direction.NORTH.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        controller.trafficLightStates[Direction.SOUTH.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
    
    if controller.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH != 0:

        controller.rightTurnLightStates[Direction.NORTH.value] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
        
        controller.rightTurnLightStates[Direction.SOUTH.value] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
        
        await controller._broadcast_state()
        
        await asyncio.sleep(controller.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH / controller.simulationSpeedMultiplier)
        
        controller.rightTurnLightStates[Direction.NORTH.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
        
        controller.rightTurnLightStates[Direction.SOUTH.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    
    await controller._broadcast_state()

async def run_horizontal_sequence(controller: TrafficLightController) -> None:
    """
    Executes a traffic light sequence for horizontal (East-West) traffic flow.
    
    This function controls the traffic light states for East-West directions, including:
    1. Waiting for North-South right turns to complete
    2. Running main traffic light sequence (Red -> Red+Amber -> Green -> Amber -> Red)
    3. Activating right turn signals for East-West traffic

    Use of simulationSpeedMultiplier, in order to speed up simulation synchronously.
    
    Parameters:
        controller: TrafficLightController instance managing the traffic states
    """

    while (controller.rightTurnLightStates[Direction.NORTH.value][TrafficLightSignal.ON.value] or 
           controller.rightTurnLightStates[Direction.SOUTH.value][TrafficLightSignal.ON.value]):
        
        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
    
    if controller.HORIZONTAL_SEQUENCE_LENGTH != 0:

        controller.trafficLightStates[Direction.EAST.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        controller.trafficLightStates[Direction.WEST.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
        
        controller.trafficLightStates[Direction.EAST.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: True,
            TrafficLightSignal.GREEN.value: False
        }

        controller.trafficLightStates[Direction.WEST.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: True,
            TrafficLightSignal.GREEN.value: False
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
        
        controller.trafficLightStates[Direction.EAST.value] = {
            TrafficLightSignal.RED.value: False,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: True
        }

        controller.trafficLightStates[Direction.WEST.value] = {
            TrafficLightSignal.RED.value: False,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: True
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.HORIZONTAL_SEQUENCE_LENGTH / controller.simulationSpeedMultiplier)
        
        controller.trafficLightStates[Direction.EAST.value] = {
            TrafficLightSignal.RED.value: False,
            TrafficLightSignal.AMBER.value: True,
            TrafficLightSignal.GREEN.value: False
        }

        controller.trafficLightStates[Direction.WEST.value] = {
            TrafficLightSignal.RED.value: False,
            TrafficLightSignal.AMBER.value: True,
            TrafficLightSignal.GREEN.value: False
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
        
        controller.trafficLightStates[Direction.EAST.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        controller.trafficLightStates[Direction.WEST.value] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        await controller._broadcast_state()

        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
    
    if controller.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH != 0:

        controller.rightTurnLightStates[Direction.EAST.value] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
        
        controller.rightTurnLightStates[Direction.WEST.value] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
        
        await controller._broadcast_state()
        
        await asyncio.sleep(controller.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH / controller.simulationSpeedMultiplier)
        
        controller.rightTurnLightStates[Direction.EAST.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
        
        controller.rightTurnLightStates[Direction.WEST.value] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    
    await controller._broadcast_state()

async def run_pedestrian_event(controller: TrafficLightController) -> None:
    """
    Executes a pedestrian crossing event sequence.
    
    This function controls the traffic light states for all directions during a pedestrian crossing event:
    1. Sets all traffic lights to red
    2. Disables all right turn signals
    3. Activates pedestrian crossing signals for all directions
    4. Waits for pedestrian crossing duration
    5. Deactivates pedestrian crossing signals

    Use of simulationSpeedMultiplier, in order to speed up simulation synchronously.
    
    Parameters:
        controller: TrafficLightController instance managing the traffic states
    """

    for d in [Direction.NORTH.value, Direction.EAST.value, Direction.SOUTH.value, Direction.WEST.value]:
        
        controller.trafficLightStates[d] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        controller.rightTurnLightStates[d] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
                
        await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)
        
        controller.pedestrianLightStates[d] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
    
    await controller._broadcast_state()
    
    await asyncio.sleep(controller.pedestrianDuration / controller.simulationSpeedMultiplier)
    
    for d in [Direction.NORTH.value, Direction.EAST.value, Direction.SOUTH.value, Direction.WEST.value]:
        
        controller.pedestrianLightStates[d] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    
    await controller._broadcast_state()

async def run_traffic_loop(controller: TrafficLightController) -> None:
    """
    Runs the main traffic light control loop alternating between vertical (N-S) and horizontal (E-W) sequences.

    This function:
    1. Tracks gaps (light sequence changes) and events (pedestrian crossings) per minute
    2. Calculates probability of pedestrian event for each gap based on:
       - Remaining pedestrian events needed this minute
       - Remaining gaps available this minute 
       - User-configured pedestrian events per minute (from client)
       - Formula: p_gap = remaining_events / remaining_gaps
    3. Randomizes pedestrian events according to calculated probability
       where probability is influenced by user-defined pedestrian frequency
    4. Maintains timing by resetting counters every 60 seconds
    5. Executes light sequences and pedestrian events in alternating pattern:
       vertical -> gap -> (maybe pedestrian) -> horizontal -> gap -> (maybe pedestrian)
    
    Parameters:
        controller: TrafficLightController managing the traffic states
    """

    maxGapsPerMinute = controller.get_max_gaps_per_minute()

    loop = asyncio.get_event_loop()

    minute_start = loop.time()

    gaps_this_minute = 0

    events_this_minute = 0

    while True:

        await run_vertical_sequence(controller)

        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
        
        gaps_this_minute += 1

        now = loop.time()
        
        if now - minute_start >= 60:
            minute_start = now
            gaps_this_minute = 0
            events_this_minute = 0

        remaining_gaps = maxGapsPerMinute - gaps_this_minute
        
        remaining_events = controller.pedestrianPerMinute - events_this_minute
        
        p_gap = (remaining_events / remaining_gaps) if remaining_gaps > 0 else 0

        if random.random() < p_gap:
            await run_pedestrian_event(controller)
            events_this_minute += 1

        await run_horizontal_sequence(controller)
        
        await asyncio.sleep(controller.gap / controller.simulationSpeedMultiplier)
        
        gaps_this_minute += 1

        now = loop.time()
        
        if now - minute_start >= 60:
            minute_start = now
            gaps_this_minute = 0
            events_this_minute = 0

        remaining_gaps = maxGapsPerMinute - gaps_this_minute
        
        remaining_events = controller.pedestrianPerMinute - events_this_minute
        
        p_gap = (remaining_events / remaining_gaps) if remaining_gaps > 0 else 0

        if random.random() < p_gap:
            await asyncio.sleep(4 / controller.simulationSpeedMultiplier)
            await run_pedestrian_event(controller)
            events_this_minute += 1