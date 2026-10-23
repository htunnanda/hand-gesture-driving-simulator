# Hand Gesture Driving Simulator
## Module Interface Specification (Draft v2)

### 1. Shared Data Format

All modules should use Member 4's Dataclass and Enum format.

The authoritative definitions are in:
`control-algorithm/control_interface.py`

The following is the current Member 4 interface.

```python
from dataclasses import dataclass
from enum import Enum

class Lane(Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"

class TrackingStatus(Enum):
    VALID = "VALID"
    LOST = "LOST"

class SwipeState(Enum):
    READY = "READY"
    SWIPE_DETECTED = "SWIPE_DETECTED"
    LANE_CHANGE = "LANE_CHANGE"
    WAIT_FOR_RESET = "WAIT_FOR_RESET"

class GameState(Enum):
    CALIBRATING = "CALIBRATING"
    WAITING_FOR_FIST = "WAITING_FOR_FIST"
    PLAYING = "PLAYING"
    STOPPED = "STOPPED"
    GAME_OVER = "GAME_OVER"

@dataclass
class TrackingInput:
    detected: bool
    landmarks: list[list[float]]
    hand_x: float
    timestamp: float
    tracking_status: TrackingStatus

@dataclass
class InferenceInput:
    gesture: str
    confidence: float
    valid: bool
    timestamp: float
    openness: float

@dataclass
class ControlCommand:
    lane: Lane
    throttle: float
    stop: bool
    valid: bool
    timestamp: float
```

### 2. Computer Vision Output

Member 1 provides TrackingInput.

```python
tracking = TrackingInput(
    detected=True,
    landmarks=[[0.5, 0.4] for _ in range(21)],
    hand_x=0.5,
    timestamp=1.0,
    tracking_status=TrackingStatus.VALID
)
```

### 3. Machine Learning Output

Member 3 provides InferenceInput.

```python
inference = InferenceInput(
    gesture="OPEN_PALM",
    confidence=0.95,
    valid=True,
    timestamp=1.0,
    openness=0.85
)
```

### 4. Control Algorithm Output

Member 4 provides ControlCommand.

```python
command = ControlCommand(
    lane=Lane.LEFT,
    throttle=0.5,
    stop=False,
    valid=True,
    timestamp=1.0
)
```

### 5. Driving Game Input

Member 5 receives ControlCommand.

```python
lane = command.lane
throttle = command.throttle
stop = command.stop
```

### 6. Safety Requirements

- FIST should request a safe stop.
- Hand tracking loss should request a safe stop.
- Invalid inference should request a safe stop.
- Openness should influence driving speed.
- Lane changes should occur once per swipe.
- Another lane change requires a neutral reset.

### 7. Pending Integration Decisions

1. Confirm actual gesture labels with Member 3.
2. Confirm throttle range and speed mapping.
3. Confirm stop behavior.
4. Confirm hand landmark coordinate format.
5. Confirm timestamp units.
6. Confirm swipe detection interface.
7. Confirm shared Python import path.

The current InferenceInput includes openness but does not include swipe.

### 8. Integration Rules

- Use Member 4 dataclasses as the proposed shared interface.
- Avoid incompatible duplicate class definitions.
- Do not rename fields without team agreement.
- Add automated interface and integration tests.
- Use Pull Requests before merging changes into main.
