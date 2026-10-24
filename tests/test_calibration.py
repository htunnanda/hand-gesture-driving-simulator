import pytest
from pathlib import Path
import importlib.util
ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_FILE = ROOT / "control-algorithm" / "calibration.py"
spec = importlib.util.spec_from_file_location("calibration", CALIBRATION_FILE)
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)
def test_empty_samples_are_invalid():
    calibrator = calibration.Calibrator()

    result = calibrator.calculate_result()

    assert result.valid is False
    assert result.neutral_x == 0.0
    assert result.closed_openness == 0.0
    assert result.open_openness == 0.0

def test_calibration_result_average():
    calibrator = calibration.Calibrator()

    calibrator.add_neutral_sample(0.49)
    calibrator.add_neutral_sample(0.51)

    calibrator.add_closed_sample(0.10)
    calibrator.add_closed_sample(0.20)

    calibrator.add_open_sample(0.80)
    calibrator.add_open_sample(1.00)

    result = calibrator.calculate_result()

    assert result.valid is True
    assert result.neutral_x == 0.50
    assert result.closed_openness == pytest.approx(0.15)
    assert result.open_openness == 0.90

def test_is_ready_with_fist():
    calibrator = calibration.Calibrator()

    assert calibrator.is_ready("FIST") is True
    assert calibrator.is_ready("OPEN_PALM") is False

def test_needs_retry():
    calibrator = calibration.Calibrator()

    assert calibrator.needs_retry() is True

    calibrator.add_neutral_sample(0.5)
    calibrator.add_closed_sample(0.1)
    calibrator.add_open_sample(0.9)

    assert calibrator.needs_retry() is False


def test_reset():
    calibrator = calibration.Calibrator()

    calibrator.add_neutral_sample(0.5)
    calibrator.add_closed_sample(0.1)
    calibrator.add_open_sample(0.9)

    calibrator.reset()

    assert calibrator.neutral_samples == []
    assert calibrator.closed_samples == []
    assert calibrator.open_samples == []