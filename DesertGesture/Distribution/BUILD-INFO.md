# Windows build provenance

- Application: Desert Signal — 3D Hand Gesture Driving Simulator
- Platform: Windows x64
- Unity Editor: 6000.3.25f1
- Source commit: `066a31919ce1ad9b4d1e3b61075e0b32a0a5a09c`
- Source branch: `codex/fix-driving-simulator`
- Build/package date: 2026-10-27 (Asia/Tokyo)
- Archive: `DesertSignal-Windows.zip`, with the complete `Build/` directory at its root
- SHA-256: `a7aee2a0d4ddd5f3484332c7151ec44eba84f05f0f88fb1e149e0e5323cd050c`

The ZIP was checked for archive corruption and required EXE, UnityPlayer and game assembly files. The Windows build compiled successfully. Built-player checks passed for brake lights, smoke stopping at standstill, brake release/reset, large-vehicle collision bounds, traffic following and all four vehicle types. Gameplay was visually inspected. See the source project's VERIFICATION.md for earlier Python/UDP checks and limitations.

Verify after downloading in PowerShell:

```powershell
Get-FileHash .\DesertSignal-Windows.zip -Algorithm SHA256
```

This is the executable game package only. Python and the gesture model are provided separately in the repository. Keyboard play needs neither Python nor Unity.
