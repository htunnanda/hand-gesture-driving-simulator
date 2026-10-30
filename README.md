# Hand Gesture Driving Simulator

Python-based 2D two-lane driving game controlled using a standard webcam and hand gestures.

## Project scope
- Two lanes only: LEFT and RIGHT; player car stays near screen bottom.
- Scrolling road, traffic, overtaking and collision detection.
- Smooth lane changes: one swipe = one command; neutral reset does not reverse the lane change.
- Calibrate hand openness; FIST confirms ready; gameplay starts at speed 0.
- Hand openness controls target speed; FIST gradually slows to zero.
- Hand tracking loss triggers a safety stop.

## Stack
Python 3.11, OpenCV, MediaPipe, NumPy, Pandas, scikit-learn, Pygame and pytest.

## Member ownership
| Member | Directory | Responsibility |
|---|---|---|
| 1 | `computer-vision/` | Webcam, landmarks, tracking validity |
| 2 | `ai-dataset/` | Dataset collection, labels, preprocessing |
| 3 | `machine-learning/` | Model training, evaluation, inference |
| 4 | `control-algorithm/` | Calibration, swipe, speed, safety |
| 5 | `real-time-application/` | Pygame road, traffic, UI, collisions |
| 6 | `integration-testing/` | Continuous code reviews, Git/PR management, testing and report collection |

## Quick start
```powershell
git clone https://github.com/htunnanda/hand-gesture-driving-simulator.git
cd hand-gesture-driving-simulator
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
```
If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` instead of `python`.

**Status:** Repository foundation only. Game modules have not been implemented yet.

Read `docs/interfaces/README.md`, `docs/GIT_WORKFLOW.md`, and `docs/REPORTING.md` before development.

## Existing repository folders
Legacy placeholder folders (`hand-gesture/`, `control-logic/`, `game-features/`, `ui-ux/`, `unity-game/`) are intentionally left untouched by this setup ZIP. New Python work uses the six member folders above.
