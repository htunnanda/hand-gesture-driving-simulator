from dataclasses import dataclass
from enum import Enum


class Lane(Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


@dataclass
class ControlCommand:
    lane: Lane
    throttle: float
    stop: bool
    valid: bool
    timestamp: float


class CommandBuilder:
    def build(
        self,
        lane,
        throttle: float,
        timestamp: float,
        stopped: bool = False,
        valid: bool = True,
    ) -> ControlCommand:
        lane_value = lane.value if hasattr(lane, "value") else lane

        if lane_value == "RIGHT":
            output_lane = Lane.RIGHT
        else:
            output_lane = Lane.LEFT

        throttle = max(0.0, min(throttle, 1.0))

        if stopped or not valid:
            throttle = 0.0

        return ControlCommand(
            lane=output_lane,
            throttle=throttle,
            stop=stopped,
            valid=valid,
            timestamp=timestamp,
        )

    def safety_stop(
        self,
        lane,
        timestamp: float,
    ) -> ControlCommand:
        return self.build(
            lane=lane,
            throttle=0.0,
            timestamp=timestamp,
            stopped=True,
            valid=False,
        )