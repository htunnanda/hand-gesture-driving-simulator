from enum import Enum


class Lane(Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class GameState(Enum):
    CALIBRATING = "CALIBRATING"
    WAITING_FOR_FIST = "WAITING_FOR_FIST"
    PLAYING = "PLAYING"
    STOPPED = "STOPPED"
    GAME_OVER = "GAME_OVER"


class ControlAlgorithm:
    def __init__(
        self,
        speed_controller,
        swipe_detector,
        calibrator=None,
        initial_lane: Lane = Lane.LEFT,
    ):
        self.speed_controller = speed_controller
        self.swipe_detector = swipe_detector
        self.calibrator = calibrator

        self.current_lane = initial_lane
        self.game_state = GameState.CALIBRATING

    def finish_calibration(self) -> bool:
        if self.calibrator is None:
            self.game_state = GameState.WAITING_FOR_FIST
            return True

        result = self.calibrator.calculate_result()

        if not result.valid:
            self.game_state = GameState.CALIBRATING
            return False

        self.speed_controller.closed_openness = result.closed_openness
        self.speed_controller.open_openness = result.open_openness
        self.swipe_detector.neutral_x = result.neutral_x

        self.game_state = GameState.WAITING_FOR_FIST
        return True

    def confirm_ready(self, gesture: str) -> bool:
        if self.game_state != GameState.WAITING_FOR_FIST:
            return False

        if gesture != "FIST":
            return False

        self.game_state = GameState.PLAYING
        return True

    def update_lane(self, hand_x: float) -> Lane:
        if self.game_state != GameState.PLAYING:
            return self.current_lane

        direction = self.swipe_detector.detect_swipe(hand_x)

        if direction.value == "LEFT":
            if self.current_lane != Lane.LEFT:
                self.current_lane = Lane.LEFT
                self.swipe_detector.start_lane_change()

        elif direction.value == "RIGHT":
            if self.current_lane != Lane.RIGHT:
                self.current_lane = Lane.RIGHT
                self.swipe_detector.start_lane_change()

        return self.current_lane

    def finish_lane_change(self):
        self.swipe_detector.finish_lane_change()

    def update_neutral_reset(self, hand_x: float) -> bool:
        return self.swipe_detector.update_reset(hand_x)

    def update_speed(
        self,
        openness: float,
        hand_detected: bool,
        valid: bool,
        gesture: str,
    ) -> float:
        if self.game_state != GameState.PLAYING:
            return 0.0

        if not hand_detected or not valid:
            self.game_state = GameState.STOPPED
            return self.speed_controller.safety_stop()

        if gesture == "FIST":
            return self.speed_controller.brake()

        return self.speed_controller.update(
            openness=openness,
            hand_detected=hand_detected,
            valid=valid,
        )

    def safety_stop(self):
        self.game_state = GameState.STOPPED
        return self.speed_controller.safety_stop()

    def game_over(self):
        self.game_state = GameState.GAME_OVER
        return self.speed_controller.safety_stop()

    def reset(self):
        self.game_state = GameState.CALIBRATING
        self.current_lane = Lane.LEFT

        self.speed_controller.reset()
        self.swipe_detector.reset()

        if self.calibrator is not None:
            self.calibrator.reset()