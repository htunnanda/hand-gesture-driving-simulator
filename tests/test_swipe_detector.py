from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
SWIPE_FILE = ROOT / "control-algorithm" / "swipe_detector.py"

spec = importlib.util.spec_from_file_location(
    "swipe_detector",
    SWIPE_FILE,
)

swipe_detector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(swipe_detector)


def test_left_swipe_detection():
    detector = swipe_detector.SwipeDetector(
        neutral_x=0.5,
        swipe_threshold=0.15,
    )

    result = detector.detect_swipe(0.30)

    assert result == swipe_detector.SwipeDirection.LEFT
    assert detector.state == swipe_detector.SwipeState.SWIPE_DETECTED


def test_right_swipe_detection():
    detector = swipe_detector.SwipeDetector(
        neutral_x=0.5,
        swipe_threshold=0.15,
    )

    result = detector.detect_swipe(0.70)

    assert result == swipe_detector.SwipeDirection.RIGHT
    assert detector.state == swipe_detector.SwipeState.SWIPE_DETECTED


def test_no_swipe_near_neutral():
    detector = swipe_detector.SwipeDetector(
        neutral_x=0.5,
        swipe_threshold=0.15,
    )

    result = detector.detect_swipe(0.55)

    assert result == swipe_detector.SwipeDirection.NONE
    assert detector.state == swipe_detector.SwipeState.READY


def test_swipe_state_flow():
    detector = swipe_detector.SwipeDetector(neutral_x=0.5)

    detector.detect_swipe(0.70)

    assert detector.state == swipe_detector.SwipeState.SWIPE_DETECTED

    detector.start_lane_change()

    assert detector.state == swipe_detector.SwipeState.LANE_CHANGE

    detector.finish_lane_change()

    assert detector.state == swipe_detector.SwipeState.WAIT_FOR_RESET


def test_neutral_reset():
    detector = swipe_detector.SwipeDetector(
        neutral_x=0.5,
        reset_threshold=0.05,
    )

    detector.detect_swipe(0.70)
    detector.start_lane_change()
    detector.finish_lane_change()

    reset = detector.update_reset(0.52)

    assert reset is True
    assert detector.state == swipe_detector.SwipeState.READY
    assert detector.last_direction == swipe_detector.SwipeDirection.NONE


def test_no_double_swipe_before_reset():
    detector = swipe_detector.SwipeDetector(neutral_x=0.5)

    first = detector.detect_swipe(0.70)
    second = detector.detect_swipe(0.30)

    assert first == swipe_detector.SwipeDirection.RIGHT
    assert second == swipe_detector.SwipeDirection.NONE