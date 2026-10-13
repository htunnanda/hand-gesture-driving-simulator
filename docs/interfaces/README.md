# Shared data interface (v0.1 proposal)

Agree on exact formats before independent modules are integrated. Examples below are illustrative; timestamps are monotonic seconds.

## Member 1 -> Members 2/3/4: tracking output
```json
{
  "detected": true,
  "landmarks": [[0.5, 0.5, 0.0]],
  "hand_x": 0.5,
  "timestamp": 0.0,
  "tracking_status": "VALID"
}
```
`landmarks` must contain **21** ordered MediaPipe landmarks when detected (example shows only one). `hand_x` is normalized [0,1]. On lost tracking use `detected=false`, `landmarks=[]`, `tracking_status="LOST"`; never reuse stale input.

## Member 2 -> Member 3: dataset
Record `sample_id`, features/landmarks, `gesture_label`, anonymized `participant_id`, `session_id`, and `split`. Avoid leakage from neighboring video frames and the same participant across evaluation splits where possible.

**Decision needed:** Members 2, 3 and 4 choose either FIST/OPEN/PARTIAL classification or continuous openness regression. A continuous speed controller needs a continuous openness estimate or another documented mapping.

## Member 3 -> Member 4: inference output
```json
{"gesture": "FIST", "confidence": 0.95, "valid": true, "timestamp": 0.0}
```
If continuous openness is used, add `openness` in [0,1] and document its calibration.

## Member 4 -> Member 5: control command
```json
{"lane": "LEFT", "throttle": 0.0, "stop": false, "valid": true, "timestamp": 0.0}
```
`lane` is the **target** lane (LEFT/RIGHT). `throttle` is target speed fraction [0,1]. `stop` is safety stop. The Pygame application animates lane changes smoothly rather than teleporting.

## Gesture and game state rules
- Swipe: `READY -> SWIPE_DETECTED -> LANE_CHANGE -> WAIT_FOR_RESET -> READY`.
- Return to neutral must not cause a reverse swipe; neutral dwell re-arms detection.
- Swipe toward the current lane does nothing.
- Game: `CALIBRATING -> WAITING_FOR_FIST -> PLAYING -> STOPPED/GAME_OVER`.
- FIST in WAITING_FOR_FIST confirms readiness; FIST in PLAYING reduces target speed toward zero.
- Hand lost means safety stop.

## Resolve before coding
1. Who calculates continuous openness and how is it calibrated?
2. How are commands transported (direct calls, queues, etc.)?
3. Who applies speed smoothing and at what update rate?
4. What timeout and confidence values mark tracking as lost?
