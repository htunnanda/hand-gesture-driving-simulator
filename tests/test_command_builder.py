from pathlib import Path
import importlib.util

import pytest


ROOT = Path(__file__).resolve().parents[1]
COMMAND_FILE = ROOT / "control-algorithm" / "command_builder.py"

spec = importlib.util.spec_from_file_location(
    "command_builder",
    COMMAND_FILE,
)

command_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(command_builder)


def test_normal_command():
    builder = command_builder.CommandBuilder()

    command = builder.build(
        lane="LEFT",
        throttle=0.5,
        timestamp=1.0,
    )

    assert command.lane == command_builder.Lane.LEFT
    assert command.throttle == pytest.approx(0.5)
    assert command.stop is False
    assert command.valid is True
    assert command.timestamp == pytest.approx(1.0)


def test_right_lane():
    builder = command_builder.CommandBuilder()

    command = builder.build(
        lane="RIGHT",
        throttle=0.7,
        timestamp=2.0,
    )

    assert command.lane == command_builder.Lane.RIGHT


def test_throttle_max_clamp():
    builder = command_builder.CommandBuilder()

    command = builder.build(
        lane="LEFT",
        throttle=2.0,
        timestamp=1.0,
    )

    assert command.throttle == pytest.approx(1.0)


def test_throttle_min_clamp():
    builder = command_builder.CommandBuilder()

    command = builder.build(
        lane="LEFT",
        throttle=-1.0,
        timestamp=1.0,
    )

    assert command.throttle == pytest.approx(0.0)


def test_stopped_command_has_zero_throttle():
    builder = command_builder.CommandBuilder()

    command = builder.build(
        lane="LEFT",
        throttle=0.8,
        timestamp=1.0,
        stopped=True,
    )

    assert command.stop is True
    assert command.throttle == 0.0


def test_invalid_command_has_zero_throttle():
    builder = command_builder.CommandBuilder()

    command = builder.build(
        lane="RIGHT",
        throttle=0.8,
        timestamp=1.0,
        valid=False,
    )

    assert command.valid is False
    assert command.throttle == 0.0


def test_safety_stop():
    builder = command_builder.CommandBuilder()

    command = builder.safety_stop(
        lane="RIGHT",
        timestamp=5.0,
    )

    assert command.lane == command_builder.Lane.RIGHT
    assert command.throttle == 0.0
    assert command.stop is True
    assert command.valid is False