class SpeedController:
    def __init__(
        self,
        closed_openness: float = 0.0,
        open_openness: float = 1.0,
        smoothing: float = 0.2,
    ):
        self.closed_openness = closed_openness
        self.open_openness = open_openness
        self.smoothing = smoothing
        self.current_throttle = 0.0

    def _clamp(self, value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(value, maximum))

    def openness_to_throttle(self, openness: float) -> float:
        if self.open_openness <= self.closed_openness:
            return 0.0

        normalized = (
            (openness - self.closed_openness)
            / (self.open_openness - self.closed_openness)
        )

        return self._clamp(normalized, 0.0, 1.0)

    def update(
        self,
        openness: float,
        hand_detected: bool = True,
        valid: bool = True,
    ) -> float:
        if not hand_detected or not valid:
            self.current_throttle = 0.0
            return 0.0

        target_throttle = self.openness_to_throttle(openness)

        self.current_throttle += (
            target_throttle - self.current_throttle
        ) * self.smoothing

        self.current_throttle = self._clamp(
            self.current_throttle,
            0.0,
            1.0,
        )

        return self.current_throttle

    def brake(self) -> float:
        self.current_throttle += (
            0.0 - self.current_throttle
        ) * self.smoothing

        if self.current_throttle < 0.01:
            self.current_throttle = 0.0

        return self.current_throttle

    def safety_stop(self) -> float:
        self.current_throttle = 0.0
        return self.current_throttle

    def reset(self):
        self.current_throttle = 0.0