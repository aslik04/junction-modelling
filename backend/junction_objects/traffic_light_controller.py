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
            
        else:

            main_vertical, main_horizontal, vertical_right, horizontal_right = self.get_sequence_lengths()
            
            self.VERTICAL_SEQUENCE_LENGTH = main_vertical
            self.HORIZONTAL_SEQUENCE_LENGTH = main_horizontal
            self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = vertical_right
            self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = horizontal_right

    def get_sequence_lengths(self) -> tuple:
        """
        
        """

        if self.traffic_settings is not None:

            traffic_settings = self.traffic_settings

            if traffic_settings.get("traffic-light-enable", False):

                sequences = traffic_settings.get("sequences", {})

                self.VERTICAL_SEQUENCE_LENGTH = int(traffic_settings.get("vertical_main_green", self.VERTICAL_SEQUENCE_LENGTH)) / sequences
                self.HORIZONTAL_SEQUENCE_LENGTH = int(traffic_settings.get("horizontal_main_green", self.HORIZONTAL_SEQUENCE_LENGTH)) / sequences
                self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = int(traffic_settings.get("vertical_right_green", self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH)) / sequences
                self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = int(traffic_settings.get("horizontal_right_green", self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH)) / sequences
                
        main_vertical = main_horizontal = vertical_right = horizontal_right = 0

        increment = 4

        if self.vehicle_data:

            north = self.vehicle_data.get("north", {})
            south = self.vehicle_data.get("south", {})
            east = self.vehicle_data.get("east", {})
            west = self.vehicle_data.get("west", {})

            vertical_total = (north.get("forward", 0) + north.get("left", 0) +
                              south.get("forward", 0) + south.get("left", 0))
            
            horizontal_total = (east.get("forward", 0) + east.get("left", 0) +
                                west.get("forward", 0) + west.get("left", 0))
            
            vertical_right_total = north.get("right", 0) + south.get("right", 0)

            horizontal_right_total = east.get("right", 0) + west.get("right", 0)

            total = vertical_total + horizontal_total + vertical_right_total + horizontal_right_total
            
            if total > 0:

                raw_main_vertical = 60 * (vertical_total / total)
                raw_main_horizontal = 60 * (horizontal_total / total)
                raw_vertical_right = 60 * (vertical_right_total / total)
                raw_horizontal_right = 60 * (horizontal_right_total / total)

                main_vertical = math.ceil(raw_main_vertical / increment)

                main_horizontal = math.ceil(raw_main_horizontal / increment)

                vertical_right = math.ceil(raw_vertical_right / increment)

                horizontal_right = math.ceil(raw_horizontal_right / increment)

        return main_vertical, main_horizontal, vertical_right, horizontal_right

    def update_vehicle_data(self, vehicle_data: Dict[str, Any]) -> None:
        """
        
        """

        self.vehicle_data = vehicle_data

        main_vertical, main_horizontal, vertical_right, horizontal_right = self.get_sequence_lengths()
        
        self.VERTICAL_SEQUENCE_LENGTH = main_vertical
        self.HORIZONTAL_SEQUENCE_LENGTH = main_horizontal
        self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = vertical_right
        self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = horizontal_right
        
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