# Member 4 — Control Algorithm

Implement calibration, FIST-ready detection, swipe state machine, neutral reset, smooth speed mapping and hand-loss safety. Output documented commands for Member 5.
# Member 4 — Control Algorithm

## Overview

This module handles the vehicle control logic for the hand gesture driving simulator.

## Implemented features

- Shared control interface definitions
- Calibration for:
  - Neutral hand position
  - Closed-hand openness
  - Open-hand openness
- FIST ready confirmation
- Calibration retry/reset logic
- Swipe detection:
  - LEFT
  - RIGHT
  - Neutral reset
  - Double/reverse swipe prevention
- Speed control:
  - Openness to throttle mapping
  - Speed smoothing
  - Brake behavior
- Safety behavior:
  - Stop when hand tracking is lost
  - Stop when input is invalid
- Game/control state handling
- Control command output for Member 5

## Main files

- `control_interface.py`
  - Shared input/output data structures

- `calibration.py`
  - Calibration and ready-check logic

- `swipe_detector.py`
  - Swipe detection state machine

- `speed_controller.py`
  - Speed mapping, smoothing, braking and safety stop

- `controller.py`
  - Integrated control algorithm

- `command_builder.py`
  - Builds final control commands for the real-time application

## Data flow

```text
Member 1
Hand Tracking
    ↓
Member 3
Gesture + Openness
    ↓
Member 4
Control Algorithm
    ↓
lane / throttle / stop / valid / timestamp
    ↓
Member 5
Real-Time Application