from enum import Enum


class SwipeState(Enum):
    READY = "READY"
    SWIPE_DETECTED = "SWIPE_DETECTED"
    LANE_CHANGE = "LANE_CHANGE"
    WAIT_FOR_RESET = "WAIT_FOR_RESET"


class SwipeDirection(Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    NONE = "NONE"


class SwipeDetector:
    def __init__(
        self,
        neutral_x: float = 0.5,
        swipe_threshold: float = 0.15,
        reset_threshold: float = 0.05,
    ):
        self.neutral_x = neutral_x
        self.swipe_threshold = swipe_threshold
        self.reset_threshold = reset_threshold

        self.state = SwipeState.READY
        self.last_direction = SwipeDirection.NONE

    def detect_swipe(self, hand_x: float) -> SwipeDirection:
        offset = hand_x - self.neutral_x

        if self.state == SwipeState.READY:
            if offset <= -self.swipe_threshold:
                self.state = SwipeState.SWIPE_DETECTED
                self.last_direction = SwipeDirection.LEFT
                return SwipeDirection.LEFT

            if offset >= self.swipe_threshold:
                self.state = SwipeState.SWIPE_DETECTED
                self.last_direction = SwipeDirection.RIGHT
                return SwipeDirection.RIGHT

        return SwipeDirection.NONE

    def start_lane_change(self):
        if self.state == SwipeState.SWIPE_DETECTED:
            self.state = SwipeState.LANE_CHANGE

    def finish_lane_change(self):
        if self.state == SwipeState.LANE_CHANGE:
            self.state = SwipeState.WAIT_FOR_RESET

    def update_reset(self, hand_x: float) -> bool:
        if self.state != SwipeState.WAIT_FOR_RESET:
            return False

        offset = abs(hand_x - self.neutral_x)

        if offset <= self.reset_threshold:
            self.state = SwipeState.READY
            self.last_direction = SwipeDirection.NONE
            return True

        return False

    def reset(self):
        self.state = SwipeState.READY
        self.last_direction = SwipeDirection.NONE