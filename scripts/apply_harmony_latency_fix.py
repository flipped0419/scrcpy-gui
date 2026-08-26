from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one match in {relative}, found {count}: {old[:160]!r}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# The upstream GUI intentionally adds a 100 ms video buffer to Desktop mode.
# That is useful for smoothing jitter, but it makes the native HarmonyOS PC
# pointer feel noticeably behind the physical UHID mouse. Keep the buffer for
# ordinary virtual-display sessions and use scrcpy's zero-buffer default for
# HarmonyOS PC mode so it matches the low-latency command-line setup we tested.
replace_once(
    "src-tauri/src/commands.rs",
    '''             args.push(format!("--new-display={}x{}/{}", w, h, dpi));
             args.push("--video-buffer=100".to_string());

             // Huawei PC mode owns the desktop shell once CastPlusDisplay is''',
    '''             args.push(format!("--new-display={}x{}/{}", w, h, dpi));
             if !harmony_desktop {
                 args.push("--video-buffer=100".to_string());
             }

             // Huawei PC mode owns the desktop shell once CastPlusDisplay is''',
)

print("HarmonyOS PC mode latency fix applied: video buffer disabled for Harmony sessions.")
