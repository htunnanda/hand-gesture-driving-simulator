
# Hand Gesture Driving Simulator
## Module Interface Specification (Draft v1)

### 1. Computer Vision Output

Webcam မှ Hand Landmark Data ထုတ်ပေးမယ်။

```python
hand_data = {
    "hand_detected": True,
    "landmarks": [(0.5, 0.4), (0.6, 0.3)],
    "timestamp": 0.0
}
```

- landmarks: normalized (x, y) coordinates
- hand_detected: True / False
- timestamp: seconds

### 2. Gesture Recognition Output

```python
gesture_data = {
    "hand_detected": True,
    "gesture": "OPEN_PALM",
    "swipe": "NONE",
    "openness": 1.0
}
```

Allowed gesture values:
- OPEN_PALM
- FIST
- UNKNOWN

Allowed swipe values:
- LEFT
- RIGHT
- NONE

### 3. Control Algorithm Output

```python
control_data = {
    "lane": "LEFT",
    "throttle": 0.6,
    "stop": False,
    "valid": True,
    "timestamp": 0.0
}
```

- `lane`: target lane, exactly `LEFT` / `RIGHT`
- `throttle`: target speed fraction in [0, 1]; the game maps this to its
  configured speed range
- `stop`: `True` requests a safety stop; `False` allows a stopped game to
  resume
- `valid`: `True` / `False`
- `timestamp`: monotonic time in seconds; stale commands are rejected

### 4. Game Input

Pygame receives `control_data` and updates:
- Player lane
- Vehicle speed from `throttle`
- Traffic movement
- Collision detection

### 5. Safety Rules

- FIST → `throttle = 0`
- OPEN_PALM → `throttle` based on openness
- LEFT swipe → change to left lane
- RIGHT swipe → change to right lane
- `stop = True` or invalid, stale, or lost control input → safe stop
- No repeated lane change until hand returns to neutral

### 6. Integration Rules

- All modules must follow the agreed data formats.
- Do not rename interface keys without team agreement.
- Add automated tests for control behavior.
- Use Pull Requests for integration.
