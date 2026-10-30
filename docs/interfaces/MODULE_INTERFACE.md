
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
    "target_speed": 60.0,
    "brake": False
}
```

- lane: LEFT / RIGHT
- target_speed: non-negative value, game speed units
- brake: True / False

### 4. Game Input

Pygame receives `control_data` and updates:
- Player lane
- Vehicle speed
- Traffic movement
- Collision detection

### 5. Safety Rules

- FIST → target_speed = 0
- OPEN_PALM → speed based on openness
- LEFT swipe → change to left lane
- RIGHT swipe → change to right lane
- Hand not detected → target_speed = 0
- No repeated lane change until hand returns to neutral

### 6. Integration Rules

- All modules must follow the agreed data formats.
- Do not rename interface keys without team agreement.
- Add automated tests for control behavior.
- Use Pull Requests for integration.
