from dataclasses import dataclass


@dataclass
class CalibrationResult:
    neutral_x: float
    closed_openness: float
    open_openness: float
    valid: bool


class Calibrator:
    def __init__(self):
        self.neutral_samples = []
        self.closed_samples = []
        self.open_samples = []

    def add_neutral_sample(self, hand_x: float):
        self.neutral_samples.append(hand_x)

    def add_closed_sample(self, openness: float):
        self.closed_samples.append(openness)

    def add_open_sample(self, openness: float):
        self.open_samples.append(openness)

    def calculate_result(self) -> CalibrationResult:
        if not self.neutral_samples or not self.closed_samples or not self.open_samples:
            return CalibrationResult(
                neutral_x=0.0,
                closed_openness=0.0,
                open_openness=0.0,
                valid=False,
            )

        neutral_x = sum(self.neutral_samples) / len(self.neutral_samples)
        closed_openness = sum(self.closed_samples) / len(self.closed_samples)
        open_openness = sum(self.open_samples) / len(self.open_samples)

        return CalibrationResult(
            neutral_x=neutral_x,
            closed_openness=closed_openness,
            open_openness=open_openness,
            valid=True,
        )
    
    def is_ready(self, gesture: str) -> bool:
        return gesture == "FIST"