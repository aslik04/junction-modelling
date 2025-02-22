import asyncio
import json
import random

class TrafficLightLogic:
    def __init__(self):
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
        self.VERTICAL_SEQUENCE_LENGTH = 5        # Green phase for north/south
        self.HORIZONTAL_SEQUENCE_LENGTH = 5       # Green phase for east/west

        self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH = 5
        self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH = 5

        # -------------------------------
        #  Pedestrian Activation
        #  - pedestrianPerMinute: desired pedestrian activations per minute.
        #  - When a pedestrian event occurs, pedestrian lights are on for a fixed 3 seconds.
        #  - There is a fixed gap (self.gap seconds) after each cycle (vertical or horizontal) during which a pedestrian event may occur.
        # -------------------------------
        self.pedestrianPerMinute = 3  # Change this to set the desired number of pedestrian events per minute
        self.pedestrianDuration = 2   # Fixed 3-second crossing
        self.gap = 1                  # Gap (in seconds) after each cycle

        self._broadcast_callback = None

    def set_broadcast_callback(self, cb):
        self._broadcast_callback = cb

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
            await asyncio.sleep(1)
        # Red→green transition (2 sec)
        self.trafficLightStates["north"] = {"red": True, "amber": False, "green": False}
        self.trafficLightStates["south"] = {"red": True, "amber": False, "green": False}
        await self._broadcast_state()
        await asyncio.sleep(1)
        self.trafficLightStates["north"] = {"red": True, "amber": True, "green": False}
        self.trafficLightStates["south"] = {"red": True, "amber": True, "green": False}
        await self._broadcast_state()
        await asyncio.sleep(1)
        # Green phase
        self.trafficLightStates["north"] = {"red": False, "amber": False, "green": True}
        self.trafficLightStates["south"] = {"red": False, "amber": False, "green": True}
        await self._broadcast_state()
        await asyncio.sleep(self.VERTICAL_SEQUENCE_LENGTH)
        # Green→amber→red transition (2 sec)
        self.trafficLightStates["north"] = {"red": False, "amber": True, "green": False}
        self.trafficLightStates["south"] = {"red": False, "amber": True, "green": False}
        await self._broadcast_state()
        await asyncio.sleep(1)
        self.trafficLightStates["north"] = {"red": True, "amber": False, "green": False}
        self.trafficLightStates["south"] = {"red": True, "amber": False, "green": False}
        await self._broadcast_state()
        await asyncio.sleep(1)
        # Right-turn phase
        self.rightTurnLightStates["north"] = {"off": False, "on": True}
        self.rightTurnLightStates["south"] = {"off": False, "on": True}
        await self._broadcast_state()
        await asyncio.sleep(self.VERTICAL_RIGHT_TURN_SEQUENCE_LENGTH)
        self.rightTurnLightStates["north"] = {"off": True, "on": False}
        self.rightTurnLightStates["south"] = {"off": True, "on": False}
        await self._broadcast_state()

    async def run_horizontal_sequence(self):
        while self.rightTurnLightStates["north"]["on"] or self.rightTurnLightStates["south"]["on"]:
            await asyncio.sleep(1)
        # Red→green transition (2 sec)
        self.trafficLightStates["east"] = {"red": True, "amber": False, "green": False}
        self.trafficLightStates["west"] = {"red": True, "amber": False, "green": False}
        await self._broadcast_state()
        await asyncio.sleep(1)
        self.trafficLightStates["east"] = {"red": True, "amber": True, "green": False}
        self.trafficLightStates["west"] = {"red": True, "amber": True, "green": False}
        await self._broadcast_state()
        await asyncio.sleep(1)
        # Green phase
        self.trafficLightStates["east"] = {"red": False, "amber": False, "green": True}
        self.trafficLightStates["west"] = {"red": False, "amber": False, "green": True}
        await self._broadcast_state()
        await asyncio.sleep(self.HORIZONTAL_SEQUENCE_LENGTH)
        # Green→amber→red transition (2 sec)
        self.trafficLightStates["east"] = {"red": False, "amber": True, "green": False}
        self.trafficLightStates["west"] = {"red": False, "amber": True, "green": False}
        await self._broadcast_state()
        await asyncio.sleep(1)
        self.trafficLightStates["east"] = {"red": True, "amber": False, "green": False}
        self.trafficLightStates["west"] = {"red": True, "amber": False, "green": False}
        await self._broadcast_state()
        await asyncio.sleep(1)
        # Right-turn phase
        self.rightTurnLightStates["east"] = {"off": False, "on": True}
        self.rightTurnLightStates["west"] = {"off": False, "on": True}
        await self._broadcast_state()
        await asyncio.sleep(self.HORIZONTAL_RIGHT_TURN_SEQUENCE_LENGTH)
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
            self.pedestrianLightStates[d] = {"off": False, "on": True}
        await self._broadcast_state()
        await asyncio.sleep(self.pedestrianDuration)
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
            await asyncio.sleep(self.gap)
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
            await asyncio.sleep(self.gap)
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
