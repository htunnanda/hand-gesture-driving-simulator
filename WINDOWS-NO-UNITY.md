# Windows game for members without Unity

## Option A: download only (keyboard demo)

1. Download [DesertSignal-Windows.zip](https://github.com/htunnanda/hand-gesture-driving-simulator/raw/refs/heads/codex/windows-no-unity/DesertGesture/Distribution/DesertSignal-Windows.zip).
2. Extract the ZIP completely. Open `Build/DesertSignal.exe`.
3. Press Enter, then use A/D, W and S/Space. No Unity or Python installation is needed for keyboard play.

Windows x64 build only; this package is not a macOS, Linux or mobile application. Keep all files beside the EXE. Do not launch from the ZIP viewer.

## Option B: repository checkout and hand gestures

From an existing checkout (commit or safely preserve your own changes before switching branches):

```powershell
cd "$env:USERPROFILE\hand-gesture-driving-simulator"
git fetch origin
git switch codex/windows-no-unity
git pull --ff-only origin codex/windows-no-unity
cd DesertGesture
Expand-Archive -LiteralPath .\Distribution\DesertSignal-Windows.zip -DestinationPath . -Force
.\Play.cmd
```

The extraction replaces files in `DesertGesture/Build`; close the game first. The ZIP contains `Build/` at its root so this command puts the EXE where `Play.cmd` expects it.

For webcam control, install Python 3.11 or 3.12 and run these from `DesertGesture`:

```powershell
.\Setup-Python.cmd
.\Run-Camera.cmd
```

Wait for setup to finish successfully before starting the camera bridge. Leave the bridge running while playing. FIST brakes, PALM starts/boosts, LEFT/RIGHT switch lanes. Camera preview Q or terminal Ctrl+C stops the bridge. Only one camera bridge and one game should run at a time. The game receives local UDP on 127.0.0.1:5055.

## Troubleshooting

- **EXE missing:** extract the ZIP; `Build` is intentionally excluded from Git as loose files.
- **Missing DLL/data:** extract the whole ZIP again and keep all companion files together.
- **Camera/model OFFLINE with keyboard game:** expected until the Python bridge is running.
- **No module named cv2:** finish `Setup-Python.cmd`, then restart `Run-Camera.cmd`. The bridge also retries failed startup every three seconds.
- **Camera unavailable:** close other camera apps and check the selected webcam; the bridge accepts `--camera 1` if another index is needed.
- **Hand UNKNOWN:** keep a clear hand in view and improve lighting. It does not necessarily mean the model is broken.

See [DesertGesture/README.md](DesertGesture/README.md) for full source/build details. The source remains available for members with Unity; members receiving this ZIP do not need to rebuild.
