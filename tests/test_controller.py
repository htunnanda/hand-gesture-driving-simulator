from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, filename):
    path = ROOT / "control-algorithm" / filename

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


controller_module = load_module(
    "controller",
    "controller.py",
)

speed_module = load_module(
    "speed_controller",
    "speed_controller.py",
)

swipe_module = load_module(
    "swipe_detector",
    "swipe_detector.py",
)

calibration_module = load_module(
    "calibration",
    "calibration.py",
)


def create_controller():
    speed = speed_module.SpeedController(
        closed_openness=0.0,
        open_openness=1.0,
        smoothing=0.2,
    )

    swipe = swipe_module.SwipeDetector(
        neutral_x=0.5,
        swipe_threshold=0.15,
    )

    calibrator = calibration_module.Calibrator()

    return controller_module.ControlAlgorithm(
        speed_controller=speed,
        swipe_detector=swipe,
        calibrator=calibrator,
    )


def test_initial_state():
    controller = create_controller()

    assert controller.game_state == controller_module.GameState.CALIBRATING
    assert controller.current_lane == controller_module.Lane.LEFT


def test_valid_calibration():
    controller = create_controller()

    controller.calibrator.add_neutral_sample(0.5)
    controller.calibrator.add_closed_sample(0.1)
    controller.calibrator.add_open_sample(0.9)

    result = controller.finish_calibration()

    assert result is True
    assert (
        controller.game_state
        == controller_module.GameState.WAITING_FOR_FIST
    )


def test_invalid_calibration():
    controller = create_controller()

    result = controller.finish_calibration()

    assert result is False
    assert controller.game_state == controller_module.GameState.CALIBRATING


def test_fist_starts_game():
    controller = create_controller()

    controller.game_state = controller_module.GameState.WAITING_FOR_FIST

    result = controller.confirm_ready("FIST")

    assert result is True
    assert controller.game_state == controller_module.GameState.PLAYING


def test_non_fist_does_not_start_game():
    controller = create_controller()

    controller.game_state = controller_module.GameState.WAITING_FOR_FIST

    result = controller.confirm_ready("OPEN_PALM")

    assert result is False
    assert (
        controller.game_state
        == controller_module.GameState.WAITING_FOR_FIST
    )


def test_right_lane_change():
    controller = create_controller()

    controller.game_state = controller_module.GameState.PLAYING

    lane = controller.update_lane(0.70)

    assert lane == controller_module.Lane.RIGHT


def test_swipe_toward_current_lane_does_nothing():
    controller = create_controller()

    controller.game_state = controller_module.GameState.PLAYING
    controller.current_lane = controller_module.Lane.LEFT

    lane = controller.update_lane(0.30)

    assert lane == controller_module.Lane.LEFT


def test_open_hand_increases_speed():
    controller = create_controller()

    controller.game_state = controller_module.GameState.PLAYING

    throttle = controller.update_speed(
        openness=1.0,
        hand_detected=True,
        valid=True,
        gesture="OPEN_PALM",
    )

    assert throttle > 0.0


def test_fist_brakes():
    controller = create_controller()

    controller.game_state = controller_module.GameState.PLAYING
    controller.speed_controller.current_throttle = 1.0

    throttle = controller.update_speed(
        openness=0.0,
        hand_detected=True,
        valid=True,
        gesture="FIST",
    )

    assert throttle < 1.0


def test_hand_lost_safety_stop():
    controller = create_controller()

    controller.game_state = controller_module.GameState.PLAYING
    controller.speed_controller.current_throttle = 0.8

    throttle = controller.update_speed(
        openness=0.8,
        hand_detected=False,
        valid=True,
        gesture="OPEN_PALM",
    )

    assert throttle == 0.0
    assert controller.game_state == controller_module.GameState.STOPPED


def test_game_over():
    controller = create_controller()

    controller.game_state = controller_module.GameState.PLAYING
    controller.speed_controller.current_throttle = 0.8

    throttle = controller.game_over()

    assert throttle == 0.0
    assert controller.game_state == controller_module.GameState.GAME_OVER