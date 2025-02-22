import math

class Car:
    def __init__(self, direction, lane, speed, turn_type, jd):
        """
        direction: "north", "east", "south", or "west"
        lane: int lane index
        speed: float speed (pixels/frame)
        turn_type: "forward", "left", or "right"
        jd: dict with geometry from getJunctionData
        """

        self.direction = direction
        self.speed = speed
        self.turn_type = turn_type
        self.jd = jd

        # For left & right, override lane
        if turn_type == "left":
            lane = 0
        elif turn_type == "right":
            lane = jd["numOfLanes"] - 1
        elif turn_type not in ["forward", "left", "right"]:
            raise ValueError("Invalid turn type")

        self.lane = lane

        self.width = jd["widthOfCar"]   # e.g. 16
        self.height = jd["heightOfCar"] # e.g. 40

        # Car “front” states:
        self.completedLeft = False
        # rightTurnPhase => 0..2 for multi-phase right turn
        self.rightTurnPhase = 0
        self.rightTurnInitialAngle = 0.0
        self.currentRightTurnAngle = 0.0

        # Once crossing the stop line, do not re-stop if the light changes.
        self.passedStopLine = False

        # Place the car off-canvas. (x,y) is the "front" of the car in direction of travel.
        if direction == "north":
            self.x = jd["leftVertical"] + jd["pixelWidthOfLane"] * (lane + 0.5)
            self.y = jd["canvasHeight"] + self.height
            self.rightTurnInitialAngle = 0.0

        elif direction == "east":
            self.x = -self.width
            self.y = jd["topHorizontal"] + jd["pixelWidthOfLane"] * (lane + 0.5)
            self.rightTurnInitialAngle = math.pi / 2

        elif direction == "south":
            self.x = jd["rightVertical"] - jd["pixelWidthOfLane"] * (lane + 0.5)
            self.y = -self.height
            self.rightTurnInitialAngle = math.pi

        elif direction == "west":
            self.x = jd["canvasWidth"] + self.width
            self.y = jd["bottomHorizontal"] - jd["pixelWidthOfLane"] * (lane + 0.5)
            self.rightTurnInitialAngle = -math.pi / 2

        else:
            raise ValueError("Invalid direction")

        self.currentRightTurnAngle = self.rightTurnInitialAngle

    def update(self, traffic_lights, right_turn_lights, all_cars):
        """
        1) If car hasn’t passed stop line:
           - forward/left need main green
           - right needs arrow on
           else clamp at line

        2) If beyond line or allowed => move:
           - forward => _move_forward
           - left => _move_left_turn
           - right => multi-phase logic (phase 0=straight to pivot, 1=arc, 2=done)

        3) Then queue behind the car in front (gap = car.height + 5).
        """
        # 1) If not passed stop line, check if we can proceed or must clamp.
        if not self.passedStopLine:
            if self.turn_type in ["forward", "left"]:
                # needs main light green
                allowed = traffic_lights.get(self.direction, {}).get("green", False)
                if not allowed:
                    stopLine = self.get_stop_line()
                    if not self.can_pass_stop_line(stopLine):
                        self.clamp_to_stop_line(stopLine)
                        self.queue_behind_car(all_cars)
                        return
            else:
                # turn_type == right
                arrowOn = right_turn_lights.get(self.direction, {}).get("on", False)
                if not arrowOn:
                    stopLine = self.get_stop_line()
                    if not self.can_pass_stop_line(stopLine):
                        self.clamp_to_stop_line(stopLine)
                        self.queue_behind_car(all_cars)
                        return

        # 2) Movement logic
        if self.turn_type == "forward":
            self._move_forward()
        elif self.turn_type == "left":
            self._move_left_turn()
        else:
            self._move_right_turn(all_cars)

        # Check if we crossed the stop line
        line = self.get_stop_line()
        if self.is_beyond_line(line):
            self.passedStopLine = True

        # 3) Enforce gap behind the car in front
        self.queue_behind_car(all_cars)

    # ------------------------------
    # Stop line / queue logic
    # ------------------------------
    def get_stop_line(self):
        pw = self.jd["pixelWidthOfLane"]
        offset = pw * 1.25 + 25
        if self.direction == "north":
            return self.jd["bottomHorizontal"] + offset
        elif self.direction == "east":
            return self.jd["leftVertical"] - offset
        elif self.direction == "south":
            return self.jd["topHorizontal"] - offset
        elif self.direction == "west":
            return self.jd["rightVertical"] + offset
        return 0

    def can_pass_stop_line(self, line):
        # Check next step
        if self.direction == "north":
            return (self.y - self.speed) >= line
        elif self.direction == "east":
            return (self.x + self.speed) <= line
        elif self.direction == "south":
            return (self.y + self.speed) <= line
        elif self.direction == "west":
            return (self.x - self.speed) >= line
        return True

    def clamp_to_stop_line(self, line):
        if self.direction == "north":
            self.y = line
        elif self.direction == "east":
            self.x = line
        elif self.direction == "south":
            self.y = line
        elif self.direction == "west":
            self.x = line

    def is_beyond_line(self, line):
        if self.direction == "north":
            return self.y < line
        elif self.direction == "east":
            return self.x > line
        elif self.direction == "south":
            return self.y > line
        elif self.direction == "west":
            return self.x < line
        return False

    def queue_behind_car(self, all_cars):
        """
        Keep a gap = (self.height + 5) behind the front car in the same lane/direction.
        """
        totalGap = self.height + 5
        best_front_car = None
        for c in all_cars:
            if c is self:
                continue
            if (c.direction == self.direction) and (c.lane == self.lane):
                # c is "ahead" if it’s further along in the direction of travel
                if self.direction == "north":
                    if c.y < self.y:  # smaller y => c is ahead
                        if (best_front_car is None) or (c.y > best_front_car.y):
                            best_front_car = c
                elif self.direction == "south":
                    if c.y > self.y:
                        if (best_front_car is None) or (c.y < best_front_car.y):
                            best_front_car = c
                elif self.direction == "east":
                    if c.x > self.x:
                        if (best_front_car is None) or (c.x < best_front_car.x):
                            best_front_car = c
                elif self.direction == "west":
                    if c.x < self.x:
                        if (best_front_car is None) or (c.x > best_front_car.x):
                            best_front_car = c

        if best_front_car is None:
            return

        # Check distance from self’s front to that car’s front
        if self.direction == "north":
            dist = self.y - best_front_car.y
            if dist < totalGap:
                self.y = best_front_car.y + totalGap
        elif self.direction == "south":
            dist = best_front_car.y - self.y
            if dist < totalGap:
                self.y = best_front_car.y - totalGap
        elif self.direction == "east":
            dist = best_front_car.x - self.x
            if dist < totalGap:
                self.x = best_front_car.x - totalGap
        elif self.direction == "west":
            dist = self.x - best_front_car.x
            if dist < totalGap:
                self.x = best_front_car.x + totalGap

    # ------------------------------
    # Movement (forward/left/right)
    # ------------------------------
    def _move_forward(self):
        if self.direction == "north":
            self.y -= self.speed
        elif self.direction == "south":
            self.y += self.speed
        elif self.direction == "east":
            self.x += self.speed
        elif self.direction == "west":
            self.x -= self.speed

    def _move_left_turn(self):
        jd = self.jd
        margin = 10
        top = jd["topHorizontal"]
        bottom = jd["bottomHorizontal"]
        left = jd["leftVertical"]
        right = jd["rightVertical"]

        if not self.completedLeft:
            if self.direction == "north":
                if (self.y - self.speed) <= (bottom - margin):
                    self.y = bottom - margin
                    self.direction = "west"
                    self.completedLeft = True
                else:
                    self.y -= self.speed
            elif self.direction == "east":
                if (self.x + self.speed) >= (left + margin):
                    self.x = left + margin
                    self.direction = "north"
                    self.completedLeft = True
                else:
                    self.x += self.speed
            elif self.direction == "south":
                if (self.y + self.speed) >= (top + margin):
                    self.y = top + margin
                    self.direction = "east"
                    self.completedLeft = True
                else:
                    self.y += self.speed
            elif self.direction == "west":
                if (self.x - self.speed) <= (right - margin):
                    self.x = right - margin
                    self.direction = "south"
                    self.completedLeft = True
                else:
                    self.x -= self.speed
        else:
            self._move_forward()

    def _move_right_turn(self, all_cars):
        jd = self.jd
        margin = 15
        top = jd["topHorizontal"]
        bottom = jd["bottomHorizontal"]
        left = jd["leftVertical"]
        right = jd["rightVertical"]

        # Move in an arc based on current angle
        self.x += self.speed * math.sin(self.currentRightTurnAngle)
        self.y += -self.speed * math.cos(self.currentRightTurnAngle)

        if self.rightTurnPhase == 0:
            if self.direction == "north" and self.y <= bottom - margin:
                self.y = bottom - margin
                self.rightTurnPhase = 1
                self.currentRightTurnAngle += math.pi / 4

            elif self.direction == "east" and self.x >= left + margin:
                self.x = left + margin
                self.rightTurnPhase = 1
                self.currentRightTurnAngle += math.pi / 4

            elif self.direction == "south" and self.y >= top + margin:
                self.y = top + margin
                self.rightTurnPhase = 1
                self.currentRightTurnAngle += math.pi / 4

            elif self.direction == "west" and self.x <= right - margin:
                self.x = right - margin
                self.rightTurnPhase = 1
                self.currentRightTurnAngle += math.pi / 4

        elif self.rightTurnPhase == 1:
            if self.direction == "north" and self.x >= right - margin:
                self.direction = "east"
                self.rightTurnPhase = 2
                self.currentRightTurnAngle += math.pi / 4
                
            elif self.direction == "east" and self.y >= bottom - margin:
                self.direction = "south"
                self.rightTurnPhase = 2
                self.currentRightTurnAngle += math.pi / 4

            elif self.direction == "south" and self.x <= left + margin:
                self.direction = "west"
                self.rightTurnPhase = 2
                self.currentRightTurnAngle += math.pi / 4

            elif self.direction == "west" and self.y <= top - margin:
                self.direction = "north"
                self.rightTurnPhase = 2
                self.currentRightTurnAngle += math.pi / 4

        else:
            # Phase 2 => Just move forward in new direction
            self._move_forward()

    # --------------
    # Helpers for right-turn pivot/arc
    # --------------
    def _queued_behind_phase0(self, all_cars):
        """
        Returns True if there is a right-turn car in the same lane/direction
        ahead of us that is still in phase 0.
        """
        for c in all_cars:
            if c is self:
                continue
            if c.direction == self.direction and c.lane == self.lane and c.turn_type == "right":
                if c.rightTurnPhase == 0:
                    # check c is ahead
                    if self.direction == "north" and c.y < self.y:
                        return True
                    if self.direction == "south" and c.y > self.y:
                        return True
                    if self.direction == "east" and c.x > self.x:
                        return True
                    if self.direction == "west" and c.x < self.x:
                        return True
        return False

    def _at_pivot_line(self):
        """
        Return True if we've reached some pivot coordinate in the intersection
        to start turning. Adjust logic as needed.
        """
        jd = self.jd
        margin = 15
        # For example, for 'north', pivot halfway between bottomHorizontal and topHorizontal:
        # That might be the vertical center or some fraction. Tweak as needed.
        if self.direction == "north":
            pivotY = jd["bottomHorizontal"] - margin
            return self.y <= pivotY
        elif self.direction == "east":
            pivotX = jd["leftVertical"] + margin
            return self.x >= pivotX
        elif self.direction == "south":
            pivotY = jd["topHorizontal"] + margin
            return self.y >= pivotY
        elif self.direction == "west":
            pivotX = jd["rightVertical"] - margin
            return self.x <= pivotX
        return False

    def _has_completed_arc(self):
        """
        If we want to treat the arc as done once we pass some boundary or get
        near a new direction. For example, once the x or y coordinate crosses
        a certain threshold. Tweak as needed.
        """
        jd = self.jd
        margin = 15
        if self.direction == "north":
            # Done turning once x >= rightVertical - margin
            return (self.x >= jd["rightVertical"] - margin)
        elif self.direction == "east":
            return (self.y >= jd["bottomHorizontal"] - margin)
        elif self.direction == "south":
            return (self.x <= jd["leftVertical"] + margin)
        elif self.direction == "west":
            return (self.y <= jd["topHorizontal"] + margin)
        return False

    def to_dict(self):
        return {
            "direction": self.direction,
            "lane": self.lane,
            "speed": self.speed,
            "turnType": self.turn_type,
            "x": self.x,
            "y": self.y,
            "currentRightTurnAngle": self.currentRightTurnAngle
        }
