"""

"""

import json
import math
from typing import Dict, Any
from .enums import Direction, TrafficLightSignal

class TrafficLightController:
    """
    
    """
    
    def __init__(self):
        """
        
        """

        self.simulationSpeedMultiplier = 1.0

        self.use_default_traffic_settings = False

        self.vehicle_data = None
        self.junction_settings = None
        self.traffic_settings = None

        self.trafficLightStates: Dict[str, Dict[str, bool]] = {
            Direction.NORTH.value: {TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False},
            Direction.EAST.value:  {TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False},
            Direction.SOUTH.value: {TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False},
            Direction.WEST.value:  {TrafficLightSignal.RED.value: True, TrafficLightSignal.AMBER.value: False, TrafficLightSignal.GREEN.value: False},
        }

        self.rightTurnLightStates: Dict[str, Dict[str, bool]] = {
            Direction.NORTH.value: {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False},
            Direction.EAST.value:  {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False},
            Direction.SOUTH.value: {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False},
            Direction.WEST.value:  {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False},
        }

        self.pedestrianLightStates: Dict[str, Dict[str, bool]] = {
            Direction.NORTH.value: {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False},
            Direction.EAST.value:  {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False},
            Direction.SOUTH.value: {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False},
            Direction.WEST.value:  {TrafficLightSignal.OFF.value: True, TrafficLightSignal.ON.value: False},
        }

        self.VERTICAL_SEQUENCE_LENGTH = 0
        self.HORIZONTAL_SEQUENCE_LENGTH = 0
        self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = 0
        self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = 0

        self.pedestrianPerMinute = 0
        self.pedestrianDuration = 0

        pedestrian_frequency, pedestrian_duration = self.get_pedestrian_data()

        self.pedestrianPerMinute = pedestrian_frequency
        self.pedestrianDuration = pedestrian_duration

        self.gap = 1

        self._broadcast_callback = None

    def set_broadcast_callback(self, cb):
        self._broadcast_callback = cb

    def update_traffic_settings(self, traffic_settings: Dict[str, Any], use_default: bool = False) -> None:
        """
        
        """

        self.traffic_settings = traffic_settings
        self.use_default_traffic_settings = use_default

        if traffic_settings.get("traffic-light-enable", False) and (not use_default) :

            sequences = traffic_settings.get("sequences", {})

            self.VERTICAL_SEQUENCE_LENGTH = int(traffic_settings.get("vertical_main_green", self.VERTICAL_SEQUENCE_LENGTH)) / sequences
            self.HORIZONTAL_SEQUENCE_LENGTH = int(traffic_settings.get("horizontal_main_green", self.HORIZONTAL_SEQUENCE_LENGTH)) / sequences
            self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = int(traffic_settings.get("vertical_right_green", self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH)) / sequences
            self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = int(traffic_settings.get("horizontal_right_green", self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH)) / sequences
        
        else :
            self.VERTICAL_SEQUENCE_LENGTH = 0
            self.HORIZONTAL_SEQUENCE_LENGTH = 0
            self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = 0
            self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = 0
            

    def update_vehicle_data(self, vehicle_data: Dict[str, Any]) -> None:
        """
        
        """

        self.vehicle_data = vehicle_data
        
    def update_junction_settings(self, junction_settings: Dict[str, Any]) -> None:
        """
        
        """

        self.junction_settings = junction_settings

        pedestrian_frequency, pedestrian_duration = self.get_pedestrian_data()
        
        self.pedestrianPerMinute = pedestrian_frequency
        
        self.pedestrianDuration = pedestrian_duration

    def get_pedestrian_data(self) -> tuple:
        """
        
        """

        pedestrian_frequency = pedestrian_duration = 0

        if self.junction_settings:

            pedestrian_duration = self.junction_settings.get("pedestrian_duration")
            
            pedestrian_frequency = self.junction_settings.get("pedestrian_frequency")
        
        return pedestrian_frequency, pedestrian_duration

    def updateDerivedStates(self) -> None:
        """
        
        """

        if any(self.pedestrianLightStates[d.value]["on"] for d in Direction):
            for d in Direction:
                self.trafficLightStates[d.value] = {
                    TrafficLightSignal.RED.value: True,
                    TrafficLightSignal.AMBER.value: False,
                    TrafficLightSignal.GREEN.value: False
                }
                self.rightTurnLightStates[d.value] = {
                    TrafficLightSignal.OFF.value: True,
                    TrafficLightSignal.ON.value: False
                }

    async def _broadcast_state(self) -> None:
        """
        
        """

        self.updateDerivedStates()

        if not self._broadcast_callback:
            return
        
        message = {
            "trafficLightStates": self.trafficLightStates,
            "rightTurnLightStates": self.rightTurnLightStates,
            "pedestrianLightStates": self.pedestrianLightStates,
        }

        data_str = json.dumps(message)

        await self._broadcast_callback(data_str)

    def get_cycle_times(self) -> tuple:
        """
        
        """

        verticalCycleTime = (5 * self.gap) + self.VERTICAL_SEQUENCE_LENGTH + self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH
        
        horizontalCycleTime = (5 * self.gap) + self.HORIZONTAL_SEQUENCE_LENGTH + self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH
        
        return verticalCycleTime, horizontalCycleTime

    def get_max_gaps_per_minute(self) -> float:
        """
        
        """
        
        verticalCycleTime, horizontalCycleTime = self.get_cycle_times()
        
        totalCycleTime = verticalCycleTime + horizontalCycleTime + (2 * self.pedestrianDuration)
        
        return 2 * (60 / totalCycleTime)