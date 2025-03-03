"""

"""

import asyncio
import random
from traffic_light_controller import TrafficLightController
from ..enums import Direction, TrafficLightSignal

async def run_vertical_sequence(controller: TrafficLightController) -> None:
    """

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

    """

    for d in [Direction.NORTH.value, Direction.EAST.value, Direction.SOUTH.value, Direction.WEST.value]:
        
        controller.trafficLightStates[d] = {
            TrafficLightSignal.RED.value: True,
            TrafficLightSignal.AMBER.value: False,
            TrafficLightSignal.GREEN.value: False
        }

        controller.rightTurnLightStates[d] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
        
        controller.leftTurnLightStates[d] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
        
        await asyncio.sleep(0.5 / controller.simulationSpeedMultiplier)
        
        controller.pedestrianLightStates[d] = {TrafficLightSignal.OFF.value: False, TrafficLightSignal.ON.value: True}
    
    await controller._broadcast_state()
    
    await asyncio.sleep(controller.pedestrianDuration / controller.simulationSpeedMultiplier)
    
    for d in [Direction.NORTH.value, Direction.EAST.value, Direction.SOUTH.value, Direction.WEST.value]:
        
        controller.pedestrianLightStates[d] = {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False}
    
    await controller._broadcast_state()

async def run_traffic_loop(controller: TrafficLightController) -> None:
    """
    
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