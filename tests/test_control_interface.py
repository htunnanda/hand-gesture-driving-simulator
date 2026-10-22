from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
CONTROL_FILE = ROOT / "control-algorithm" / "control_interface.py"

spec = importlib.util.spec_from_file_location("control_interface", CONTROL_FILE)
control_interface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control_interface)

def test_lane_values():
    assert control_interface.Lane.LEFT.value == "LEFT"
    assert control_interface.Lane.RIGHT.value == "RIGHT"

def test_control_command_creation():
    command = control_interface.ControlCommand(
        lane=control_interface.Lane.LEFT,
        throttle=0.5,
        stop=False,
        valid=True,
        timestamp=1.0,
    )

    assert command.lane == control_interface.Lane.LEFT
    assert command.throttle == 0.5
    assert command.stop is False
    assert command.valid is True
    assert command.timestamp == 1.0    

def test_inference_input_creation():
    inference = control_interface.InferenceInput(
        gesture="OPEN_PALM",
        confidence=0.95,
        valid=True,
        timestamp=1.0,
        openness=0.85,
    )

    assert inference.gesture == "OPEN_PALM"
    assert inference.confidence == 0.95
    assert inference.valid is True
    assert inference.timestamp == 1.0
    assert inference.openness == 0.85

