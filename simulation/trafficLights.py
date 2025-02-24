import asyncio
import json
import random
import requests
import math
from typing import Dict, Any

class TrafficLightLogic:
    def __init__(self):
        self.simulationSpeedMultiplier = 1.0  # <--- ADD THIS

        self.vehicle_data = None  # Add this to hold vehicle input data
        # -------------------------------
        #  Traffic Light States
        # -------------------------------
        self.trafficLightStates = {
            "north": {"red": True, "amber": False, "green": False},
            "east":  {"red": True, "amber": False, "green": False},
            "south": {"red": True, "amber": False, "green": False},
            "west":  {"red": True, "amber": False, "green": False},
        }
        self.rightTurnLightStates = {
            "north": {"off": True, "on": False},
            "east":  {"off": True, "on": False},
            "south": {"off": True, "on": False},
            "west":  {"off": True, "on": False},
        }
        self.pedestrianLightStates = {
            "north": {"off": True, "on": False},
            "east":  {"off": True, "on": False},
            "south": {"off": True, "on": False},
            "west":  {"off": True, "on": False},
        }
        self.leftTurnLightStates = {
            "north": {"off": True, "on": False},
            "east":  {"off": True, "on": False},
            "south": {"off": True, "on": False},
            "west":  {"off": True, "on": False},
        }

        # -------------------------------
        #  Sequence Timings (seconds)
        #  - Each cycle consists of:
        #     • A fixed 2-sec red→green transition,
        #     • A green phase (duration set by the sequence length),
        #     • A fixed 2-sec green→amber→red transition,
        #     • A right-turn phase.
        # -------------------------------
        self.VERTICAL_SEQUENCE_LENGTH = 0       # Green phase for north/south
        self.HORIZONTAL_SEQUENCE_LENGTH = 0    # Green phase for east/west
        self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = 0
        self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = 0

        main_vertical, main_horizontal, vertical_right, horizontal_right = self.get_sequence_lengths()
        
        self.VERTICAL_SEQUENCE_LENGTH = main_vertical       # Green phase for north/south
        self.HORIZONTAL_SEQUENCE_LENGTH = main_horizontal    # Green phase for east/west

        self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = vertical_right
        self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = horizontal_right

        # -------------------------------
        #  Pedestrian Activation
        #  - pedestrianPerMinute: desired pedestrian activations per minute.
        #  - When a pedestrian event occurs, pedestrian lights are on for a fixed 3 seconds.
        #  - There is a fixed gap (self.gap seconds) after each cycle (vertical or horizontal) during which a pedestrian event may occur.
        # -------------------------------
        try:
            response = requests.get("http://127.0.0.1:5000/junction_settings_proxy")
            if response.status_code == 200:
                settings = response.json()
                self.pedestrianPerMinute = int(settings.get("pedestrian_frequency", 4))  # Ensure it's an integer
                self.pedestrianDuration = int(settings.get("pedestrian_time", 3))  # Ensure it's an integer

                print(f"✅ Pedestrian Frequency: {self.pedestrianPerMinute} per hour")
                print(f"✅ Pedestrian Duration: {self.pedestrianDuration} seconds")

            else:
                print("⚠️ Failed to fetch pedestrian settings, using defaults.")
                self.pedestrianPerMinute = 4
                self.pedestrianDuration = 3
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error fetching settings: {e}")
            self.pedestrianPerMinute = 4
            self.pedestrianDuration = 3

        self.gap = 2                # Gap (in seconds) after each cycle

        self._broadcast_callback = None

    def set_broadcast_callback(self, cb):
        self._broadcast_callback = cb

    def get_sequence_lengths(self):
        """
        Compute cycle times based on vehicle input data.
        Returns four values: main_vertical, main_horizontal, vertical_right, horizontal_right.
        """
        # Default base sequence lengths (if no vehicle data is provided)
        main_vertical = main_horizontal = vertical_right = horizontal_right = 0
        increment = 4

        if self.vehicle_data:
            north = self.vehicle_data.get("north", {})
            south = self.vehicle_data.get("south", {})
            east  = self.vehicle_data.get("east", {})
            west  = self.vehicle_data.get("west", {})

            # For main phase, assume forward and left are the main moves.
            vertical_total = (north.get("forward", 0) + north.get("left", 0) +
                            south.get("forward", 0) + south.get("left", 0))
            horizontal_total = (east.get("forward", 0) + east.get("left", 0) +
                                west.get("forward", 0) + west.get("left", 0))
            vertical_right_total = north.get("right", 0) + south.get("right", 0)
            horizontal_right_total = east.get("right", 0) + west.get("right", 0)

            total = vertical_total + horizontal_total + vertical_right_total + horizontal_right_total

            # Print intermediate values for debugging:
            print("[DEBUG] Vehicle Data Totals:")
            print("  vertical_total =", vertical_total)
            print("  horizontal_total =", horizontal_total)
            print("  vertical_right_total =", vertical_right_total)
            print("  horizontal_right_total =", horizontal_right_total)
            print("  total =", total)

            if total > 0:
                # Calculate raw green times (in seconds) for each phase
                raw_main_vertical = 60 * (vertical_total / total)
                raw_main_horizontal = 60 * (horizontal_total / total)
                raw_vertical_right = 60 * (vertical_right_total / total)
                raw_horizontal_right = 60 * (horizontal_right_total / total)

                # Print raw computed times:
                print("[DEBUG] Raw cycle times:")
                print("  raw_main_vertical =", raw_main_vertical)
                print("  raw_main_horizontal =", raw_main_horizontal)
                print("  raw_vertical_right =", raw_vertical_right)
                print("  raw_horizontal_right =", raw_horizontal_right)

                # Now quantize by increment (if desired)
                main_vertical = math.ceil(raw_main_vertical / increment)
                main_horizontal = math.ceil(raw_main_horizontal / increment)
                vertical_right = math.ceil(raw_vertical_right / increment)
                horizontal_right = math.ceil(raw_horizontal_right / increment)

        print("[DEBUG] Final sequence lengths:")
        print("  main_vertical =", main_vertical)
        print("  main_horizontal =", main_horizontal)
        print("  vertical_right =", vertical_right)
        print("  horizontal_right =", horizontal_right)
                    
        return main_vertical, main_horizontal, vertical_right, horizontal_right

    def update_vehicle_data(self, vehicle_data: Dict[str, Any]):
        """
        Update the traffic light logic with the latest vehicle input data,
        and recalculate the sequence lengths based on the new data.
        """
        self.vehicle_data = vehicle_data
        # Recalculate sequence lengths from the new vehicle data
        main_vertical, main_horizontal, vertical_right, horizontal_right = self.get_sequence_lengths()
        self.VERTICAL_SEQUENCE_LENGTH = main_vertical
        self.HORIZONTAL_SEQUENCE_LENGTH = main_horizontal
        self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = vertical_right
        self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = horizontal_right

        print("TrafficLightLogic: Vehicle data updated:", self.vehicle_data)
        print("[DEBUG] Updated sequence lengths:")
        print("  main_vertical =", self.VERTICAL_SEQUENCE_LENGTH)
        print("  main_horizontal =", self.HORIZONTAL_SEQUENCE_LENGTH)
        print("  vertical_right =", self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH)
        print("  horizontal_right =", self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH)


    def updateDerivedStates(self):
        # Compute left-turn state:
        self.leftTurnLightStates["north"] = {
            "on": self.trafficLightStates["north"]["green"] and (not self.pedestrianLightStates["east"]["on"]),
            "off": not (self.trafficLightStates["north"]["green"] and (not self.pedestrianLightStates["east"]["on"]))
        }
        self.leftTurnLightStates["east"] = {
            "on": self.trafficLightStates["east"]["green"] and (not self.pedestrianLightStates["south"]["on"]),
            "off": not (self.trafficLightStates["east"]["green"] and (not self.pedestrianLightStates["south"]["on"]))
        }
        self.leftTurnLightStates["south"] = {
            "on": self.trafficLightStates["south"]["green"] and (not self.pedestrianLightStates["west"]["on"]),
            "off": not (self.trafficLightStates["south"]["green"] and (not self.pedestrianLightStates["west"]["on"]))
        }
        self.leftTurnLightStates["west"] = {
            "on": self.trafficLightStates["west"]["green"] and (not self.pedestrianLightStates["north"]["on"]),
            "off": not (self.trafficLightStates["west"]["green"] and (not self.pedestrianLightStates["north"]["on"]))
        }
        # Pedestrian override: if a pedestrian light is on, force that direction's own lights off and force the anticlockwise left-turn off.
        if self.pedestrianLightStates["north"]["on"]:
            self.trafficLightStates["north"] = {"red": True, "amber": False, "green": False}
            self.rightTurnLightStates["north"] = {"off": True, "on": False}
            self.leftTurnLightStates["north"] = {"off": True, "on": False}
            self.leftTurnLightStates["west"] = {"off": True, "on": False}
        if self.pedestrianLightStates["east"]["on"]:
            self.trafficLightStates["east"] = {"red": True, "amber": False, "green": False}
            self.rightTurnLightStates["east"] = {"off": True, "on": False}
            self.leftTurnLightStates["east"] = {"off": True, "on": False}
            self.leftTurnLightStates["north"] = {"off": True, "on": False}
        if self.pedestrianLightStates["south"]["on"]:
            self.trafficLightStates["south"] = {"red": True, "amber": False, "green": False}
            self.rightTurnLightStates["south"] = {"off": True, "on": False}
            self.leftTurnLightStates["south"] = {"off": True, "on": False}
            self.leftTurnLightStates["east"] = {"off": True, "on": False}
        if self.pedestrianLightStates["west"]["on"]:
            self.trafficLightStates["west"] = {"red": True, "amber": False, "green": False}
            self.rightTurnLightStates["west"] = {"off": True, "on": False}
            self.leftTurnLightStates["west"] = {"off": True, "on": False}
            self.leftTurnLightStates["south"] = {"off": True, "on": False}

    async def _broadcast_state(self):
        self.updateDerivedStates()
        if not self._broadcast_callback:
            return
        message = {
            "trafficLightStates": self.trafficLightStates,
            "rightTurnLightStates": self.rightTurnLightStates,
            "pedestrianLightStates": self.pedestrianLightStates,
            "leftTurnLightStates": self.leftTurnLightStates
        }
        data_str = json.dumps(message)
        await self._broadcast_callback(data_str)

    def get_cycle_times(self):
        """
        Return the vertical and horizontal cycle times (excluding the gap).
        Each cycle consists of:
          - A 2-sec red→green transition,
          - A green phase,
          - A 2-sec green→amber→red transition,
          - A right-turn phase.
        """
        verticalCycleTime = 2 + self.VERTICAL_SEQUENCE_LENGTH + 2 + self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH
        horizontalCycleTime = 2 + self.HORIZONTAL_SEQUENCE_LENGTH + 2 + self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH
        return verticalCycleTime, horizontalCycleTime

    def get_max_gaps_per_minute(self):
        """
        Calculate the expected maximum number of gap opportunities per minute.
        A gap occurs after each cycle (vertical or horizontal), and the gap itself lasts self.gap seconds.
        We compute:
           maxVerticalGaps = 60 / (verticalCycleTime + self.gap)
           maxHorizontalGaps = 60 / (horizontalCycleTime + self.gap)
           maxGapsPerMinute = maxVerticalGaps + maxHorizontalGaps
        """
        verticalCycleTime, horizontalCycleTime = self.get_cycle_times()
        maxVerticalGaps = 60 / (verticalCycleTime + self.gap)
        maxHorizontalGaps = 60 / (horizontalCycleTime + self.gap)
        return maxVerticalGaps + maxHorizontalGaps

    async def run_vertical_sequence(self):
        while self.rightTurnLightStates["east"]["on"] or self.rightTurnLightStates["west"]["on"]:
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
        if self.VERTICAL_SEQUENCE_LENGTH is not 0:
            # Red→green transition (2 sec)
            self.trafficLightStates["north"] = {"red": True, "amber": False, "green": False}
            self.trafficLightStates["south"] = {"red": True, "amber": False, "green": False}
            await self._broadcast_state()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
            self.trafficLightStates["north"] = {"red": True, "amber": True, "green": False}
            self.trafficLightStates["south"] = {"red": True, "amber": True, "green": False}
            await self._broadcast_state()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
            # Green phase
            self.trafficLightStates["north"] = {"red": False, "amber": False, "green": True}
            self.trafficLightStates["south"] = {"red": False, "amber": False, "green": True}
            await self._broadcast_state()
            await asyncio.sleep(self.VERTICAL_SEQUENCE_LENGTH / self.simulationSpeedMultiplier)
            # Green→amber→red transition (2 sec)
            self.trafficLightStates["north"] = {"red": False, "amber": True, "green": False}
            self.trafficLightStates["south"] = {"red": False, "amber": True, "green": False}
            await self._broadcast_state()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
            self.trafficLightStates["north"] = {"red": True, "amber": False, "green": False}
            self.trafficLightStates["south"] = {"red": True, "amber": False, "green": False}
            await self._broadcast_state()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
            
        if self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH is not 0:
            # Right-turn phase
            self.rightTurnLightStates["north"] = {"off": False, "on": True}
            self.rightTurnLightStates["south"] = {"off": False, "on": True}
            await self._broadcast_state()
            await asyncio.sleep(self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH / self.simulationSpeedMultiplier)
            self.rightTurnLightStates["north"] = {"off": True, "on": False}
            self.rightTurnLightStates["south"] = {"off": True, "on": False}

        await self._broadcast_state()

    async def run_horizontal_sequence(self):
        while self.rightTurnLightStates["north"]["on"] or self.rightTurnLightStates["south"]["on"]:
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)

        if self.HORIZONTAL_SEQUENCE_LENGTH is not 0:
            # Red→green transition (2 sec)
            self.trafficLightStates["east"] = {"red": True, "amber": False, "green": False}
            self.trafficLightStates["west"] = {"red": True, "amber": False, "green": False}
            await self._broadcast_state()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
            self.trafficLightStates["east"] = {"red": True, "amber": True, "green": False}
            self.trafficLightStates["west"] = {"red": True, "amber": True, "green": False}
            await self._broadcast_state()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
            # Green phase
            self.trafficLightStates["east"] = {"red": False, "amber": False, "green": True}
            self.trafficLightStates["west"] = {"red": False, "amber": False, "green": True}
            await self._broadcast_state()
            await asyncio.sleep(self.HORIZONTAL_SEQUENCE_LENGTH / self.simulationSpeedMultiplier)
            # Green→amber→red transition (2 sec)
            self.trafficLightStates["east"] = {"red": False, "amber": True, "green": False}
            self.trafficLightStates["west"] = {"red": False, "amber": True, "green": False}
            await self._broadcast_state()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
            self.trafficLightStates["east"] = {"red": True, "amber": False, "green": False}
            self.trafficLightStates["west"] = {"red": True, "amber": False, "green": False}
            await self._broadcast_state()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)

        if self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH is not 0:
            # Right-turn phase
            self.rightTurnLightStates["east"] = {"off": False, "on": True}
            self.rightTurnLightStates["west"] = {"off": False, "on": True}
            await self._broadcast_state()
            await asyncio.sleep(self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH / self.simulationSpeedMultiplier)
            self.rightTurnLightStates["east"] = {"off": True, "on": False}
            self.rightTurnLightStates["west"] = {"off": True, "on": False}
        await self._broadcast_state()

    async def run_pedestrian_event(self):
        """
        When a pedestrian event occurs, force all traffic to red/off,
        and turn on pedestrian lights for all directions for a fixed duration.
        """
        for d in ["north", "east", "south", "west"]:
            self.trafficLightStates[d] = {"red": True, "amber": False, "green": False}
            self.rightTurnLightStates[d] = {"off": True, "on": False}
            self.leftTurnLightStates[d] = {"off": True, "on": False}
            await asyncio.sleep(0.5)
            self.pedestrianLightStates[d] = {"off": False, "on": True}
        await self._broadcast_state()
        await asyncio.sleep(self.pedestrianDuration / self.simulationSpeedMultiplier)
        for d in ["north", "east", "south", "west"]:
            self.pedestrianLightStates[d] = {"off": True, "on": False}
        await self._broadcast_state()

    async def run_traffic_loop(self):
        """
        Continuously cycle vertical then horizontal sequences.
        We maintain a per-minute counter: at the start of each minute we reset the count of gap opportunities
        and pedestrian events triggered. For each gap opportunity (after a vertical or horizontal sequence),
        we calculate:
            remaining_gaps = maxGapsPerMinute - gaps_so_far
            remaining_events = pedestrianPerMinute - events_so_far
            p_gap = remaining_events / remaining_gaps   (if remaining_gaps > 0)
        Then, using this adaptive probability, we randomly decide whether to trigger a pedestrian event.
        This method ensures that on average the number of pedestrian events per minute
        will match the pedestrianPerMinute value, with their placement chosen randomly among the gaps.
        """
        maxGapsPerMinute = self.get_max_gaps_per_minute()
        loop = asyncio.get_event_loop()
        minute_start = loop.time()
        gaps_this_minute = 0
        events_this_minute = 0

        while True:
            # Run vertical cycle then gap
            await self.run_vertical_sequence()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
            gaps_this_minute += 1

            now = loop.time()
            if now - minute_start >= 60:
                minute_start = now
                gaps_this_minute = 0
                events_this_minute = 0

            remaining_gaps = maxGapsPerMinute - gaps_this_minute
            remaining_events = self.pedestrianPerMinute - events_this_minute
            p_gap = (remaining_events / remaining_gaps) if remaining_gaps > 0 else 0

            if random.random() < p_gap:
                await self.run_pedestrian_event()
                events_this_minute += 1

            # Run horizontal cycle then gap
            await self.run_horizontal_sequence()
            await asyncio.sleep(self.gap / self.simulationSpeedMultiplier)
            gaps_this_minute += 1

            now = loop.time()
            if now - minute_start >= 60:
                minute_start = now
                gaps_this_minute = 0
                events_this_minute = 0

            remaining_gaps = maxGapsPerMinute - gaps_this_minute
            remaining_events = self.pedestrianPerMinute - events_this_minute
            p_gap = (remaining_events / remaining_gaps) if remaining_gaps > 0 else 0

            if random.random() < p_gap:
                await asyncio.sleep(4 / self.simulationSpeedMultiplier)
                await self.run_pedestrian_event()
                events_this_minute += 1
