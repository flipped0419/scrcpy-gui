# HarmonyOS PC Mode

This document describes the HarmonyOS PC Mode integration in this ScrcpyGUI fork.

## Status

The feature is experimental and firmware-dependent. It has been verified on a HarmonyOS 4.2 device using scrcpy 4.1 over USB ADB.

The goal is not to reimplement a desktop launcher. The goal is to make the phone's own Huawei / HarmonyOS PC projection framework recognize a scrcpy-created virtual display, then stream and control that native desktop with scrcpy.

## Why a normal scrcpy virtual display is not enough

A normal scrcpy virtual display is useful for launching Android apps on a secondary display, but Huawei's PC launcher performs an additional work-mode check. Starting `PcHomeLauncher` manually on an arbitrary virtual display is not sufficient to initialize the full vendor PC stack.

During testing, the key difference was the virtual display identity. When the scrcpy-created display is named `CastPlusDisplay`, the system projection components recognize it as a cast target and expose the phone's native PC Mode flow.

## Implementation

### Two server files

The fork intentionally keeps two scrcpy server files:

```text
scrcpy-server          normal scrcpy server
scrcpy-server-harmony  HarmonyOS-specific scrcpy server
```

The desktop client remains the standard scrcpy executable. ScrcpyGUI selects the server by setting `SCRCPY_SERVER_PATH` for the launched scrcpy process.

This keeps normal mirroring and normal virtual-display behavior isolated from the vendor-specific HarmonyOS change.

### Server modification

`scrcpy-server-harmony` is built from scrcpy v4.1. The build script modifies the virtual display name in:

```text
server/src/main/java/com/genymobile/scrcpy/video/NewDisplayCapture.java
```

from:

```java
createNewVirtualDisplay("scrcpy", ...)
```

to:

```java
createNewVirtualDisplay("CastPlusDisplay", ...)
```

The patched server is then compiled with scrcpy's normal Gradle build.

Reproducible build script:

```text
scripts/build_harmony_server.ps1
```

### Runtime profile

HarmonyOS PC Mode reuses the existing ScrcpyGUI Desktop Mode configuration for:

- resolution
- DPI
- bitrate
- max FPS
- video codec
- audio
- renderer
- recording
- window options

The HarmonyOS path additionally uses:

```text
--mouse=uhid
--keyboard=uhid
--shortcut-mod=rctrl
```

A practical starting profile is:

```text
1920 x 1080
240 DPI
60 FPS
```

The UI changes the stock 420 DPI desktop default to 240 DPI when HarmonyOS PC Mode is enabled, unless the user has already selected a custom DPI.

## Low-latency behavior

The upstream Desktop Mode path adds:

```text
--video-buffer=100
```

That buffer is useful for smoothing some ordinary virtual-display sessions, but it adds approximately 100 ms of visible latency. With UHID mouse input this makes the remote cursor feel delayed even though the input event itself reaches the phone quickly.

HarmonyOS PC Mode therefore does **not** add `--video-buffer=100`. It keeps scrcpy's normal low-latency rendering behavior.

## Input behavior

### Mouse

UHID mouse input is preferred because it behaves like a real physical mouse on the HarmonyOS desktop and avoids the initial absolute-coordinate mismatch seen with SDK mouse injection.

Press **Right Ctrl** to release or recapture the mouse.

The phone's pointer speed is a device-global setting. ScrcpyGUI intentionally does not modify it. If the pointer feels too fast, inspect the current value with:

```powershell
adb shell settings get system pointer_speed
```

and, if desired, change it manually, for example:

```powershell
adb shell settings put system pointer_speed -2
```

Restore the previous value when necessary.

### Keyboard and IME

UHID keyboard input gives the most native desktop behavior for English text and shortcuts.

A known Huawei/HarmonyOS limitation is that the system input method may continue to process Chinese composition while its candidate window remains hidden in PC Mode. This is controlled by the vendor desktop/input-method stack rather than by scrcpy's display capture.

Clipboard paste works as a reliable Unicode fallback.

Because this limitation is firmware-specific and Chinese input is not required for the core PC Mode feature, this fork currently keeps the simpler UHID keyboard path rather than shipping a custom IME bridge.

## Features disabled in HarmonyOS PC Mode

### Flex Display

Flex Display dynamically resizes the virtual display with the host window. The Huawei desktop stack expects a stable cast display and may relayout or recreate components when the display geometry changes.

For stability, Flex Display is disabled while HarmonyOS PC Mode is active.

### Start App

The ordinary Desktop Mode can optionally launch a selected Android package directly onto the virtual display.

HarmonyOS PC Mode does not use this option because the vendor PC launcher owns desktop initialization. Apps should be launched from the native PC desktop after the session starts.

## Session lifecycle

On supported firmware, the first recognized `CastPlusDisplay` session may present a choice between phone projection and PC Mode. After PC Mode is selected, the system may remember that preference and automatically re-enter PC Mode the next time the compatible display appears.

Display IDs are dynamic. The implementation does not rely on a fixed Android display ID.

## Compatibility

Known working environment:

- HarmonyOS 4.2
- Android API layer reporting Android 12
- scrcpy 4.1
- USB ADB
- 1920x1080 virtual display
- 240 DPI

Other Huawei / HONOR devices may use different projection services, permissions, or display heuristics. Reports for other firmware versions are welcome.

## Troubleshooting

### The window is black

Confirm that the HarmonyOS server was actually selected. ScrcpyGUI logs the server path at session startup.

The expected file is:

```text
scrcpy-server-harmony
```

For portable setups it may sit next to `scrcpy.exe`. Installer builds also carry it in the application resources.

### The phone stays in normal projection mode

Close the session and start HarmonyOS PC Mode again. On some firmware, the first recognized cast session requires manually selecting PC Mode once on the phone.

### The cursor feels delayed

Make sure the HarmonyOS path is not receiving `--video-buffer=100`. The current fork explicitly removes that buffer from HarmonyOS PC Mode.

### The cursor is too fast

This is usually the phone's physical-pointer speed, not video latency. Adjust the Android/HarmonyOS pointer speed manually if necessary.

### Chinese candidates are not visible

This is a known vendor IME behavior with physical/UHID keyboard input in PC Mode. Clipboard paste is currently the recommended fallback.

## Build from source

Prerequisites:

- Windows / PowerShell 7
- Git
- Java 17
- Android SDK platform and build tools 36
- Python 3
- Node.js 20+
- Rust / Cargo
- Tauri v2 build prerequisites

Build the Harmony server:

```powershell
pwsh ./scripts/build_harmony_server.ps1
```

Apply fork patches:

```powershell
python scripts/apply_fork_customizations.py
python scripts/apply_app_picker_improvements.py
python scripts/apply_app_names_orientation.py
python scripts/apply_harmony_desktop.py
python scripts/apply_harmony_latency_fix.py
python scripts/apply_harmony_session_behavior.py
```

Build ScrcpyGUI:

```powershell
npm ci
npm run lint
npm test
npm run tauri build
```

## Licensing

The ScrcpyGUI fork is MIT-licensed according to the repository `LICENSE` file.

The Harmony server is a derivative build of Genymobile/scrcpy v4.1 and remains subject to the Apache License 2.0. See:

- `THIRD_PARTY_NOTICES.md`
- `licenses/scrcpy-APACHE-2.0.txt`
