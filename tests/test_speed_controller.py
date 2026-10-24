from pathlib import Path
import importlib.util

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEED_FILE = ROOT / "control-algorithm" / "speed_controller.py"

spec = importlib.util.spec_from_file_location(
    "speed_controller",
    SPEED_FILE,
)

speed_controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(speed_controller)


def test_closed_hand_maps_to_zero():
    controller = speed_controller.SpeedController(
        closed_openness=0.1,
        open_openness=0.9,
    )

    throttle = controller.openness_to_throttle(0.1)

    assert throttle == pytest.approx(0.0)


def test_open_hand_maps_to_one():
    controller = speed_controller.SpeedController(
        closed_openness=0.1,
        open_openness=0.9,
    )

    throttle = controller.openness_to_throttle(0.9)

    assert throttle == pytest.approx(1.0)


def test_middle_openness_maps_to_half():
    controller = speed_controller.SpeedController(
        closed_openness=0.1,
        open_openness=0.9,
    )

    throttle = controller.openness_to_throttle(0.5)

    assert throttle == pytest.approx(0.5)


def test_throttle_is_clamped():
    controller = speed_controller.SpeedController(
        closed_openness=0.1,
        open_openness=0.9,
    )

    assert controller.openness_to_throttle(-1.0) == pytest.approx(0.0)
    assert controller.openness_to_throttle(2.0) == pytest.approx(1.0)


def test_speed_smoothing():
    controller = speed_controller.SpeedController(
        closed_openness=0.0,
        open_openness=1.0,
        smoothing=0.2,
    )

    throttle = controller.update(
        openness=1.0,
        hand_detected=True,
        valid=True,
    )

    assert throttle == pytest.approx(0.2)


def test_lost_hand_causes_safety_stop():
    controller = speed_controller.SpeedController(
        smoothing=0.2,
    )

    controller.current_throttle = 0.8

    throttle = controller.update(
        openness=1.0,
        hand_detected=False,
        valid=True,
    )

    assert throttle == 0.0
    assert controller.current_throttle == 0.0


def test_invalid_input_causes_safety_stop():
    controller = speed_controller.SpeedController()

    controller.current_throttle = 0.7

    throttle = controller.update(
        openness=0.8,
        hand_detected=True,
        valid=False,
    )

    assert throttle == 0.0


def test_brake_reduces_speed():
    controller = speed_controller.SpeedController(
        smoothing=0.2,
    )

    controller.current_throttle = 1.0

    throttle = controller.brake()

    assert throttle == pytest.approx(0.8)


def test_safety_stop_immediately_sets_zero():
    controller = speed_controller.SpeedController()

    controller.current_throttle = 0.9

    controller.safety_stop()

    assert controller.current_throttle == 0.0


def test_reset():
    controller = speed_controller.SpeedController()

    controller.current_throttle = 0.7

    controller.reset()

    assert controller.current_throttle == 0.0