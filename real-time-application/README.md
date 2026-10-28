# Pygame Game Engine

Member 5's module: a standalone, keyboard-playable two-lane driving game. The
engine does not capture webcam video, run hand tracking, or train a model.

## Architecture

The implementation is in `main.py`:

- `Lane` and `GameState` define the two lanes and the READY, PLAYING, STOPPED,
  and GAME_OVER states.
- `GameStateManager` allows only documented state transitions.
- `Road` owns lane state, scroll offsets, lane centers, and a bounded set of
  roadside objects.
- `PlayerCar` keeps target lane state separate from its screen position,
  animates lane changes using delta time, and provides the player rectangle.
- `TrafficCar` represents and draws one traffic car. `TrafficSpawner` handles
  configurable spawning, safe spacing, movement, and removal of off-screen
  cars.
- `detect_collision` performs Pygame rectangle intersection checks separately
  from traffic generation.
- `DrivingScene` coordinates input, state transitions, and simulation updates.
  It does not render UI.
- `GameRenderer` projects the road, lane markings, roadside objects, and
  traffic into a pseudo-3D perspective, and draws the player car, HUD, state
  overlays, and control warnings.
- `run_game` initializes Pygame and runs the resizable, 60 FPS application
  loop.

The visual style uses a horizon in the upper quarter, a trapezoidal highway
that widens toward the bottom, progressively shaded asphalt, an animated
center divider and solid road boundaries, desert terrain, mountain
silhouettes, perspective-scaled shrubs, and traffic cars that scale with
distance. The player is drawn as a larger rear-view sports car. It is a 2D
projection with no true 3D camera, lighting, or asset-based car models.

The default traffic spawn interval is 2.5 seconds, minimum same-lane spawn
gap is 100 pixels, and traffic speed scale is 1.0. These values can be
configured when creating `TrafficSpawner`.

## Setup and launch

Use Python 3.11 in PowerShell from the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pygame pytest
python real-time-application\main.py
```

Alternatively, install the repository's full dependency set with
`python -m pip install -r requirements.txt`. The game window starts in READY.
Press Enter or Space to begin.

## Gesture-integrated launch

To run the webcam and model integration, install the repository dependencies
and launch the integrated entry point from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe real-time-application\main_gesture_integrated.py
```

This entry point loads `machine_learning\models\gesture_model.pkl` and opens
camera index 0. Use the same virtual-environment interpreter for installation
and launch so the camera, MediaPipe, and model dependencies are available.

## Keyboard controls

| Input | Action |
|---|---|
| Enter or Space (READY) | Start |
| Left/Right arrows or A/D (PLAYING) | Request LEFT/RIGHT lane |
| Up/Down arrows or W/S (PLAYING) | Increase/decrease speed by 10 |
| Space (PLAYING) | Stop |
| Space (STOPPED) | Resume |
| R (GAME_OVER) | Restart to READY |
| Window close button | Quit from any state |

Speed is clamped to 0–100. Road markings, roadside objects, and traffic only
move while the state is PLAYING; forward movement is proportional to speed.
Lane changes are animated and cannot move beyond either of the two lanes.

## Control interface

`DrivingScene.handle_control_input` accepts a `ControlInput` object and can be
called by a future control module or a mock/test driver. It does not access a
camera. A valid `stop=True` command enters STOPPED; a fresh valid
`stop=False` command resumes PLAYING. Invalid, stale, hand-lost, or
camera-error status safely sets speed to zero and stops a running game, while
showing a warning.

The canonical Member 4 → Member 5 command contract, documented in
[`docs/interfaces/README.md`](../docs/interfaces/README.md), is:

```json
{
  "lane": "LEFT",
  "throttle": 0.0,
  "stop": false,
  "valid": true,
  "timestamp": 0.0
}
```

- `lane`: target lane, exactly `"LEFT"` or `"RIGHT"`.
- `throttle`: target speed fraction from `0.0` to `1.0`; the game maps it to
  the 0–100 speed range.
- `stop`: boolean safety-stop command.
- `valid`: boolean validity flag.
- `timestamp`: monotonic time in seconds. Inputs more than one second old or
  from the future are rejected.

Convert the agreed mapping to the engine's `ControlInput` type and pass it to
`DrivingScene.handle_control_input`. For example:

```python
import time

command = ControlInput(
    lane="RIGHT",
    throttle=0.6,
    stop=False,
    valid=True,
    timestamp=time.monotonic(),
)
scene.handle_control_input(command)
```

The repository currently launches this module as a standalone script rather
than as an installable Python package. The integrating caller must import
`ControlInput` and obtain the `DrivingScene` instance through its chosen
in-process integration point.

`hand_lost=True` and `camera_error=True` are optional status flags supported
by the Python adapter; they are not additional fields in the base shared
command. All integration remains direct in-process calls; no webcam, process
transport, or hand-tracking module is included.

## Tests

Run the complete test suite from the repository root:

```powershell
py -3.11 -m pytest
```

Run only the game-engine tests:

```powershell
py -3.11 -m pytest tests\test_perspective_renderer.py tests\test_game_lane_changes.py tests\test_game_states.py tests\test_traffic.py tests\test_game_traffic_integration.py
```

Manual visual checks: launch the game, press Enter, and raise speed with Up.
Confirm the center divider moves toward the bottom, the road widens toward
the player, and traffic cars grow as they approach. Use Left/Right to change
lanes; test collision by placing a traffic car in the player's lane with
`scene.traffic.spawn_car(...)` in a debugger or test, then verify GAME_OVER
and R-to-restart. Resize the window and verify the road and cars redraw to
the new viewport; close the window to quit.

## Implemented features and limitations

Implemented: resizable pseudo-3D two-lane road, rear-view procedural player
car, smooth lane switching,
speed-dependent scrolling, bounded roadside scenery, traffic generation in
both lanes, spawn-gap checks, rectangle-based collision detection, all four
game states, restart, speed/lane HUD, and mockable control input with
freshness validation.

Limitations: cars, mountains, and roadside items use simple Pygame shapes;
there are no downloaded assets, webcam capture, hand tracking, AI
inference/training, or external
control transport. Traffic spawning avoids close traffic and simultaneous
lane blockage at spawn time but does not promise that every future traffic
pattern is avoidable. The UI has no audio or persistent score.

The perspective renderer uses `GameRenderer.project_progress`,
`road_half_width`, and `traffic_rect`; collision detection uses the same
projected traffic rectangle as drawing. `Road.update` continues to own the
delta-time road and roadside scroll state.

## Module testing evidence

Evidence recorded 2026-10-23:

| Command | Result | Environment / notes |
|---|---|---|
| `python -m pytest -q tests\test_perspective_renderer.py tests\test_game_lane_changes.py tests\test_game_states.py tests\test_traffic.py tests\test_game_traffic_integration.py` | 25 passed | Python 3.12.10, Pygame 2.6.1 |
| `python -m pytest -q` | 26 passed, 1 failed | Existing repository setup test fails because `machine-learning/README.md` is missing; unrelated to this module |
| Headless launch with VIDEORESIZE and QUIT events | Passed | Pygame 2.6.1; startup, resize, draw, and quit exercised |

Python 3.11 is the target runtime, but it was not installed in the environment
used for the recorded test runs. Re-run the commands above with Python 3.11
before claiming Python 3.11 validation.
