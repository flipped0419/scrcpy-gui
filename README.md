<p align="center">
  <img src="icon.png" width="128" height="128" alt="ScrcpyGUI Icon">
  <br>
  <h1>ScrcpyGUI v4 — HarmonyOS PC Mode fork</h1>
  <strong>ScrcpyGUI with a native Huawei / HarmonyOS desktop-mode bridge.</strong>
</p>

<p align="center">
  <img width="850" alt="ScrcpyGUI Interface" src="https://github.com/user-attachments/assets/a416fcd3-295a-4a01-8769-6f9da429b028" />
</p>

> **Fork notice**
> This repository is a fork of [kil0bit-kb/scrcpy-gui](https://github.com/kil0bit-kb/scrcpy-gui). The upstream project provides the ScrcpyGUI v4 application; this fork adds HarmonyOS PC Mode support and several virtual-display workflow improvements.

ScrcpyGUI v4 is a modern GUI for [scrcpy](https://github.com/Genymobile/scrcpy), built with **Tauri v2**, **React 19**, and **Rust**.

## What this fork adds

- **HarmonyOS PC Mode (experimental)**
  - Creates a dedicated `CastPlusDisplay` virtual display so supported Huawei / HarmonyOS devices can enter the vendor's native PC desktop mode.
  - Uses a separate `scrcpy-server-harmony` while keeping the normal `scrcpy-server` untouched.
  - Reuses the existing Desktop Mode controls for resolution, DPI, bitrate, FPS, codec, audio, renderer, recording, and window options.
  - Defaults to a practical `1920x1080 / 240 DPI` profile when switching from the stock 420 DPI desktop default.
  - Uses UHID keyboard and mouse input, with **Right Ctrl** as the mouse-capture release shortcut.
  - Removes the normal Desktop Mode `--video-buffer=100` delay for the HarmonyOS path to preserve scrcpy's low-latency behavior.
- **Desktop app launch**
  - Optional package launch on ordinary virtual displays.
  - App picker and app-name improvements.
  - Orientation-aware virtual display launch behavior.
- **Upstream-friendly customization layer**
  - Fork changes are applied by scripts during CI so the upstream source remains easier to sync and compare.

## HarmonyOS PC Mode

### How it works

Ordinary scrcpy virtual displays are created with the name `scrcpy`. On compatible Huawei / HarmonyOS software, the vendor PC projection framework recognizes a display named `CastPlusDisplay` and can initialize its native PC desktop stack.

This fork therefore keeps two server implementations:

```text
scrcpy-server          -> normal scrcpy behavior
scrcpy-server-harmony  -> virtual display name changed to CastPlusDisplay
```

The Harmony server is built reproducibly from **scrcpy v4.1** in CI. The only scrcpy server source modification is the virtual-display name used by `NewDisplayCapture`.

For implementation details, compatibility notes, and troubleshooting, see **[docs/HARMONYOS_PC_MODE.md](docs/HARMONYOS_PC_MODE.md)**.

### Quick start

1. Enable **Developer options** and **USB debugging** on the phone.
2. Connect the phone over USB and select it in ScrcpyGUI.
3. Set **Capture Source** to **Desktop**.
4. Enable **HarmonyOS PC Mode**.
5. A good starting profile is:
   - Resolution: `1920 x 1080`
   - DPI: `240`
   - FPS: `60`
   - Bitrate: use the same value you normally use with scrcpy
6. Start the session. On devices that remember the previous projection mode, subsequent sessions may return directly to PC Mode.
7. Press **Right Ctrl** to release or recapture the UHID mouse.

### Known limitations

- Compatibility is vendor- and firmware-specific. It has been verified on a HarmonyOS 4.2 device, but other Huawei / HONOR models and firmware versions may behave differently.
- **Flex Display** is disabled in HarmonyOS PC Mode because dynamically resizing the virtual display can interfere with the vendor desktop stack.
- **Start App** is disabled in HarmonyOS PC Mode; the vendor PC launcher owns desktop initialization.
- With UHID keyboard input, some Huawei input-method builds may process Chinese composition while keeping the candidate UI hidden. Clipboard paste remains a reliable Unicode fallback.
- UHID pointer speed is controlled by the Android/HarmonyOS system. This fork does not change the device-global `pointer_speed` setting automatically.

## Core ScrcpyGUI features

This fork retains the upstream ScrcpyGUI feature set, including:

- scrcpy binary management and updates
- USB and wireless ADB connectivity
- camera / webcam mode
- HID keyboard and mouse support
- renderer selection
- recording and audio controls
- file and APK drag-and-drop
- themes and window customization
- standard Desktop Mode with Flex Display

See **[GUIDE.md](GUIDE.md)** for the general ScrcpyGUI user guide.

## Windows builds

The HarmonyOS integration currently has a dedicated Windows CI workflow:

**[Windows HarmonyOS build workflow](../../actions/workflows/windows-fork-build.yml)**

The workflow builds:

- `ScrcpyGUI.exe`
- NSIS installer
- MSI installer
- `scrcpy-server-harmony`

Until a tagged fork release is published, use the workflow artifact from a successful run.

## Development

### Prerequisites

- Node.js 20+
- Rust and Cargo
- Tauri v2 prerequisites
- Java 17
- Android SDK platform / build tools 36
- Python 3
- Git

### Build the HarmonyOS server

```powershell
pwsh ./scripts/build_harmony_server.ps1
```

This creates:

```text
src-tauri/resources/scrcpy-server-harmony
```

### Apply fork customizations

```powershell
python scripts/apply_fork_customizations.py
python scripts/apply_app_picker_improvements.py
python scripts/apply_app_names_orientation.py
python scripts/apply_harmony_desktop.py
python scripts/apply_harmony_latency_fix.py
python scripts/apply_harmony_session_behavior.py
```

Then build normally:

```powershell
npm ci
npm run lint
npm test
npm run tauri build
```

## Licensing and attribution

- ScrcpyGUI source in this repository remains under the **MIT License**; see [LICENSE](LICENSE).
- `scrcpy-server-harmony` is a modified build of [Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) v4.1 and is distributed under the **Apache License 2.0**.
- See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [licenses/scrcpy-APACHE-2.0.txt](licenses/scrcpy-APACHE-2.0.txt).

Thanks to:

- [kil0bit-kb/scrcpy-gui](https://github.com/kil0bit-kb/scrcpy-gui) — upstream GUI project
- [Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) — core Android display/control engine
- [Tauri](https://tauri.app/), [React](https://react.dev/), and [Lucide](https://lucide.dev/)

This fork is independent and is not affiliated with Huawei, HONOR, Genymobile, or the upstream ScrcpyGUI authors.
