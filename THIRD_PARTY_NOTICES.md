# Third-Party Notices

This repository is a fork of **ScrcpyGUI v4** and also builds a modified scrcpy server for HarmonyOS PC Mode.

## ScrcpyGUI

Upstream project:

- https://github.com/kil0bit-kb/scrcpy-gui

The ScrcpyGUI source is distributed under the MIT License. The original copyright notice is retained in this repository's `LICENSE` file.

## scrcpy / scrcpy-server-harmony

Upstream project:

- https://github.com/Genymobile/scrcpy
- Base version used by the HarmonyOS server build: **v4.1**

License:

- Apache License 2.0
- A copy is included at `licenses/scrcpy-APACHE-2.0.txt`.

Relevant upstream copyright notice:

```text
Copyright (C) 2018 Genymobile
Copyright (C) 2018-2026 Romain Vimont
```

### Modification made by this fork

The HarmonyOS build changes the virtual-display name in scrcpy's `NewDisplayCapture.java` from:

```text
scrcpy
```

to:

```text
CastPlusDisplay
```

This modification is applied by `scripts/build_harmony_server.ps1` before compiling `scrcpy-server-harmony`.

The purpose of the change is to let compatible Huawei / HarmonyOS firmware recognize the scrcpy-created virtual display as a cast display and initialize its vendor PC desktop mode.

No claim is made that this behavior is part of the public Huawei or HarmonyOS API surface, and compatibility may vary by firmware.

## Trademarks

Huawei, HarmonyOS, HONOR, Android, scrcpy, and other names and marks belong to their respective owners. Their use in this repository is solely descriptive. This fork is not affiliated with or endorsed by Huawei, HONOR, Genymobile, Google, or the upstream ScrcpyGUI authors.
