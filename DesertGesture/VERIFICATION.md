# Verification — 2026-10-27

- Inspected the original Pygame adapter, model mapping, shared preprocessing, dependency pins and previous repair report.
- Copied preprocessing/model unchanged. Model SHA-256: `053B6C410B334C947E83370236A4F817F28CC52C43ACAA9A28528BA9970BD775` (matches original).
- Actual RandomForest loads and predicts under the existing Python 3.12 environment with scikit-learn 1.6.1. Confirmed 63 features and numeric classes 0,1,2,3.
- Three Python tests pass: class mapping/debounce/low-confidence clearing, stale-camera boost clearing while retaining model status, and actual subprocess UDP packet sequencing plus clean shutdown.
- Actual webcam + MediaPipe 0.10.21 processing test delivered 125 status packets, including CAMERA ONLINE / MODEL ONLINE. No recognized hand was presented during this test; classification accuracy and gesture ergonomics still need a user demonstration.
- Unity 6000.3.25f1 compiled and built the Windows player successfully. Built-player testing found and fixed runtime shader stripping by including a Resources material.
- Built-player smoke test passed: lane boundaries, boost/brake priority and values, game-over/reset, swept collision bounds, all five gestures received over real loopback UDP, and UNKNOWN after sender timeout. Result is in `Build/smoke-result.txt`.
- Gameplay rendered with Direct3D 11 and was visually inspected at 1280×720. `preview.png` is an actual game frame. Camera/model are OFFLINE in this keyboard-only screenshot by design.

Limitations: procedural placeholder cars and scenery; no licensed third-party models; arcade collision envelope rather than full vehicle physics; camera preview is in a separate OpenCV window. Live gesture accuracy, extended play balance and testing on other computers remain unverified.

Sports-car update: Unity build succeeded; updated rear gameplay view visually inspected; built-player mechanics, all UDP gestures and stale timeout passed again. Original procedural wedge body, rolling alloy wheels and closer chase camera added.

Brake/mixed-traffic update: Unity build succeeded. Built-player assertions passed for brake lamps, no smoke at standstill, brake release, reset cleanup, coach/truck swept collision bounds, follower slowing and all four procedural vehicle types. Direct3D 11 gameplay preview visually checked for brake lamps, tyre smoke, sedan, sports car, cargo truck and express bus. Smoke is a stylized hard-braking effect, not a tyre physics simulation.
