# Windows 3D Simulator — Unity မလိုဘဲ Run နိုင်သော Version

This branch provides the ready-to-run **Windows x64 build** of Desert Signal for members who do not have Unity installed.

## Download and play

**[Download DesertSignal-Windows.zip (31.6 MB)](https://github.com/htunnanda/hand-gesture-driving-simulator/raw/refs/heads/codex/windows-no-unity/DesertGesture/Distribution/DesertSignal-Windows.zip)**

1. ZIP ကို download လုပ်ပြီး **Extract All** လုပ်ပါ။
2. ဖြည်ထားတဲ့ `Build` folder ထဲက **DesertSignal.exe** ကို ဖွင့်ပါ။
3. Unity သို့မဟုတ် Python မရှိလည်း keyboard နဲ့ ကစားနိုင်ပါတယ်။

Keep the entire `Build` folder together, including `DesertSignal_Data`, `UnityPlayer.dll`, `MonoBleedingEdge` and other runtime files. Do not move only the EXE, and do not run it from inside the ZIP.

| Control | Action |
|---|---|
| Enter | Start |
| A / D or left / right arrows | Change lane |
| W / up | Boost |
| S / down / Space | Brake; brake lights and high-speed tyre smoke |
| P / Escape | Pause / resume |
| R | Reset |
| K | Toggle keyboard-only mode |

Includes an orange sports car, sedan/truck/express-bus traffic, brake lights, tyre smoke and vehicle-size collision bounds.

**[Full setup and gesture-control instructions](WINDOWS-NO-UNITY.md)** · **[Build checksum and provenance](DesertGesture/Distribution/BUILD-INFO.md)**

Camera/model OFFLINE is expected when only the game is running. For hand control, set up and run the Python bridge separately. Unity is still not required.

---

## Original Python prototype documentation

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
