from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write_text(relative: str, content: str) -> None:
    (ROOT / relative).write_text(content, encoding="utf-8")


def replace_once(relative: str, old: str, new: str) -> None:
    text = read_text(relative)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one match in {relative}, found {count}: {old[:160]!r}"
        )
    write_text(relative, text.replace(old, new, 1))


# HarmonyOS PC Mode intentionally reuses the global Session Behavior settings.
# Most of these were already generated for every non-camera session by
# build_scrcpy_args(); keep explicit CI guards here so future upstream changes
# cannot silently make Harmony Desktop diverge from normal mirroring.
commands = read_text("src-tauri/src/commands.rs")
required = [
    'let can_control = config.session_mode != "camera";',
    'args.push("--stay-awake".to_string())',
    'args.push("--keep-active".to_string())',
    'args.push("--turn-screen-off".to_string())',
    'args.push("--no-power-on".to_string())',
    'args.push("--no-audio".to_string())',
    'args.push("--always-on-top".to_string())',
    'args.push("--fullscreen".to_string())',
    'args.push("--window-borderless".to_string())',
    'args.push(format!("--record={}", full_path.to_string_lossy()))',
]
for snippet in required:
    if snippet not in commands:
        raise RuntimeError(f"Shared Session Behavior support missing from commands.rs: {snippet}")

# "Remember window position" was the one Session Behavior toggle that was
# deliberately limited to mirror sessions. Harmony Desktop is also a normal
# scrcpy SDL window, so let it reuse the same saved per-device position while
# keeping ordinary virtual-desktop sessions unchanged.
replace_once(
    "src-tauri/src/commands.rs",
    '        if config.session_mode == "mirror" && !config.fullscreen.unwrap_or(false) {',
    '        if (config.session_mode == "mirror" || harmony_desktop) && !config.fullscreen.unwrap_or(false) {',
)
replace_once(
    "src-tauri/src/commands.rs",
    '    let track_pos = config_mon.session_mode == "mirror" && !config_mon.fullscreen.unwrap_or(false);',
    '    let track_pos = (config_mon.session_mode == "mirror" || (config_mon.session_mode == "desktop" && config_mon.harmony_desktop.unwrap_or(false))) && !config_mon.fullscreen.unwrap_or(false);',
)

# Update the two tooltips that previously implied these controls were limited
# to screen mirroring. The controls themselves remain shared; this just makes
# the UI description match their actual Harmony Desktop behaviour.
replace_once(
    "src/i18n/locales/en.ts",
    "        stayAwakeTooltip: 'Keep device awake while mirroring.',",
    "        stayAwakeTooltip: 'Keep the device awake during screen mirroring or HarmonyOS PC Mode.',",
)
replace_once(
    "src/i18n/locales/en.ts",
    "        screenOffTooltip: 'Turn off device screen while mirroring to save power.',",
    "        screenOffTooltip: 'Turn off the device main screen during screen mirroring or HarmonyOS PC Mode to save power.',",
)
replace_once(
    "src/i18n/locales/zh-CN.ts",
    "        stayAwakeTooltip: '镜像时保持设备常亮。',",
    "        stayAwakeTooltip: '普通投屏或鸿蒙电脑模式运行时保持设备唤醒。',",
)
replace_once(
    "src/i18n/locales/zh-CN.ts",
    "        screenOffTooltip: '镜像时关闭手机屏幕以节省电量。',",
    "        screenOffTooltip: '普通投屏或鸿蒙电脑模式运行时关闭手机主屏幕以节省电量。',",
)

print("HarmonyOS shared Session Behavior settings applied successfully.")
