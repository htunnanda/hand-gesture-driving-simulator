# Desert Signal — Hand Gesture Driving Simulator

Unity 6 presentation prototype: three-lane desert road, procedural sports cars and sandstone scenery, smooth chase camera, traffic, collision flash/sound, restart/pause, and a cyan HUD. Python owns webcam tracking and RandomForest inference; Unity owns the game. No downloaded art assets are required.

## Quick demo

1. If `Build/DesertSignal.exe` is included, open it. Otherwise open `Unity/` in Unity Hub using **6000.3.25f1**, open `Assets/Scenes/Desert.unity`, and press Play. If the scene is missing, select **Desert Signal → Create demo scene** first.
2. Press **Enter** to drive. **A/D or left/right arrows** change one lane; hold **W/up** to boost; hold **S/down/Space** to brake. **P/Escape** pauses, **R** resets to the start screen, **K** toggles keyboard-only mode. Close the window to exit.
3. Optional transport demo: run `Run-Demo-Bridge.cmd`. It cycles synthetic gestures, visibly labelled **SIMULATED**. It may crash into traffic; it is a transport demo, not an autopilot. No webcam or ML packages are needed for this mode.

## Real hand control

Use Python **3.11 or 3.12**. From this folder in PowerShell:

```powershell
python --version
python -m venv Python/.venv
./Python/.venv/Scripts/python.exe -m pip install -r Python/requirements.txt
./Python/.venv/Scripts/python.exe Python/bridge.py --preview
```

Or double-click `Setup-Python.cmd`, then `Run-Camera.cmd`. Start Unity/the built game as above. The OpenCV window shows the mirrored webcam and hand landmarks; click back into the game for keyboard controls. Press Q in the camera window, or Ctrl+C in the terminal, to stop the bridge.

On this PC the existing compatible environment can also run it without reinstalling:

```powershell
& 'C:/Users/yanpa/hand-gesture-driving-simulator/.venv/Scripts/python.exe' ./Python/bridge.py --preview
```

| Input | Action |
| --- | --- |
| LEFT / class 1 / left_dir | Move one lane left |
| RIGHT / class 3 / right_dir | Move one lane right |
| PALM / class 2 | Start from ready; hold for 145 km/h boost |
| FIST / class 0 | Hold to brake to zero |
| UNKNOWN / low confidence / missing hand | No steering; return toward 85 km/h cruise |

Brake overrides boost. Hold a direction to move only one lane; release the gesture for at least 0.3 seconds before repeating it. Direction changes can also trigger a new lane change. Predictions need confidence ≥0.70 and three consecutive matching frames. Pause and game-over require explicit keyboard/button actions; a palm does not resume a paused or crashed run. This is an arcade simulation, not a vehicle controller.

## Reuse and layout

Original inspected project: `C:/Users/yanpa/hand-gesture-driving-simulator`. This standalone companion leaves that project intact. `Python/machine_learning/preprocessing.py` and `models/gesture_model.pkl` are copied unchanged from it. Features remain 21 × xyz coordinates, wrist-centred and normalized by maximum wrist distance; class order remains fist, left_dir, palm, right_dir. Model loading was checked with scikit-learn 1.6.1. No retraining or model conversion was performed.

- `Python/bridge.py`: camera worker, preprocessing/model inference, debounce, independent status heartbeat, UDP sender.
- `Unity/Assets/Scripts/GestureReceiver.cs`: local nonblocking receiver, schema/order checks, 0.7-second timeout.
- `Unity/Assets/Scripts/DesertGame.cs`: procedural environment, player/traffic, swept longitudinal collision bounds, score, HUD and camera.
- `Unity/Assets/Editor/BuildProject.cs`: scene creation and Windows build.
- `Python/test_bridge.py`, `Unity/Assets/Scripts/RuntimeSmoke.cs`: transport and runtime checks.

To replace cars, assign visual prefabs on the Desert Signal scene object's `playerVisualPrefab` / `trafficVisualPrefab` fields. Use +Z forward, road-level origin, approximately 1.8 m width × 4 m length. Collision envelopes remain in game code. Scenery is generated in `Awake`; edit the factory there to replace mesas/cacti. Source art consists of original procedural primitives; car interiors, photoreal textures, post-processing, advanced traffic AI and an embedded webcam panel are not included. Webcam preview is a separate OpenCV window. Current HUD uses scaled immediate-mode UI for a minimal dependency prototype.

## Transport

JSON over UDP at **127.0.0.1:5055**, 20 packets/second. Unity binds loopback only; no router/firewall opening is needed. Camera images are not transmitted. Example:

```json
{"v":1,"session":"random-session-id","seq":42,"gesture":"LEFT","confidence":0.94,"camera":"ONLINE","model":"ONLINE","detail":"Tracking"}
```

`session` changes on sender restart; `seq` increases. Receiver ignores duplicate/out-of-order packets for the current live session. The last command expires after 0.7 seconds without valid packets. The independent Python sender also clears gesture when camera frames are stale, even if capture stalls. No hand means UNKNOWN while camera/model may remain ONLINE. Shutdown sends an explicit offline packet. Run only one sender and one game instance.

## Build and verify

```powershell
./Python/.venv/Scripts/python.exe -m unittest discover -s Python -v
& 'C:/Program Files/Unity/Hub/Editor/6000.3.25f1/Editor/Unity.exe' -batchmode -nographics -quit -projectPath "$PWD/Unity" -executeMethod BuildProject.Build -logFile "$PWD/build.log"
```

Unity may return control before the background build finishes; inspect `build.log`. Output is `Build/DesertSignal.exe` and its companion folders; distribute the entire Build folder. A valid local Unity license is required for editor/build use. The editor creates scene and project settings; runtime boot also works from an empty scene.

For the built-player smoke test, launch `Build/DesertSignal.exe -batchmode -nographics --smoke` and immediately run `python Python/bridge.py --demo --seconds 12` in another terminal. After about 14 seconds, `Build/smoke-result.txt` reports lane/speed/reset checks, all five UDP commands and stale timeout. This does not test real-camera recognition or visual quality.

## Troubleshooting

- **Model ONLINE, camera OFFLINE:** close Pygame/Teams/other camera users; check Windows camera privacy settings. Try `--camera 1`. Restart the bridge after correcting the issue. Model availability is reported separately from camera failure.
- **Missing MediaPipe Hands API:** install the pinned requirements in the venv. MediaPipe 0.10.35 removed the `solutions` API used by this model pipeline; this project targets 0.10.21.
- **scikit-learn version warning:** use 1.6.1, matching the saved model. Only load trusted model files.
- **HUD OFFLINE:** start Python; inspect its terminal. Confirm port 5055 is free and only one game instance is open. A missing bridge does not prevent keyboard play.
- **Hand UNKNOWN:** improve lighting, keep the entire hand visible and hold the gesture steadily. The copied model's accuracy depends on its original training data.
- **Keys do nothing:** click the Unity Game view or player window; press Enter. Pause uses P, reset uses R. Press K to exclude gesture interference.
- **Pink materials:** use this built-in-renderer project rather than importing the scripts into a URP/HDRP template without adapting the Standard materials.

Unity runtime initialization reference: https://docs.unity.com/en-us/engine/6000.0/script-reference/unityengine/runtimeinitializeonloadmethodattribute

## Sports-car visual update

The player now uses an original orange Lamborghini-inspired wedge coupe with rounded procedural bodywork, a sloping glass canopy, metallic paint, Y-shaped rear lights, engine louvers, rear diffuser, twin exhausts and five-spoke rolling wheels. Traffic includes sports cars, sedans, cargo trucks and express coaches with separate dimensions and cruising speeds. The closer chase camera makes the car easier to see. No manufacturer logos or third-party model assets are included. The visual factory is `Unity/Assets/Scripts/SportsCarVisual.cs`; prefab overrides remain supported.

## Brake effects and mixed traffic

- Hold S/down/Space or show FIST: rear Y lamps and the centre stop strip brighten, red light falls onto the road and the body dips slightly under braking.
- Braking above 35 km/h produces short, fading smoke trails at the rear tyres. Below that speed the emission stops; at standstill the brake lamps stay on while the brake is held. Pause, crash and reset clear smoke and lamps.
- Traffic cycles between sports car, sedan, three-axle cargo truck and express bus. Detailed windows, cargo doors, coach livery, rolling wheels and tail lamps distinguish them. Cruising speeds vary by type; following vehicles slow for traffic ahead.
- Truck and coach collision bounds include their full body length. Spawn spacing avoids an immediate three-lane wall. Traffic holds its lane; this remains an arcade driving prototype, not a full tyre/ABS/vehicle-physics simulation.
- `VehicleEffects.cs` and `Resources/TyreSmoke.shader` implement brake/smoke feedback. `TrafficVehicle.cs` owns vehicle models, size and speeds. The existing generic traffic prefab override replaces the visuals; custom prefabs must match the selected type's dimensions.
- Built-player regression check: `Build/DesertSignal.exe -batchmode -nographics --effects-test`. It exits with code 0 on success and writes `Build/effects-test.txt`.
- Visual QA fixture: `Build/DesertSignal.exe --traffic-capture -force-d3d11`. It shows four vehicle types with braking active, saves `preview.png`, then exits. Normal play has no forced braking or fixture traffic.
