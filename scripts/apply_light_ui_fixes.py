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
            f"Expected exactly one match in {relative}, found {count}: {old[:180]!r}"
        )
    write_text(relative, text.replace(old, new, 1))


# ---------------------------------------------------------------------------
# 1) Make scrcpy's shortcut modifier configurable for HarmonyOS PC Mode.
#    The same modifier toggles UHID mouse capture, so this is the user-facing
#    "release mouse" key. scrcpy v4.1 accepts these six single modifiers.
# ---------------------------------------------------------------------------
replace_once(
    "src/hooks/useScrcpy.ts",
    "    harmonyDesktop?: boolean;\n    rotation?: string;",
    "    harmonyDesktop?: boolean;\n    shortcutMod?: 'lctrl' | 'rctrl' | 'lalt' | 'ralt' | 'lsuper' | 'rsuper';\n    rotation?: string;",
)
replace_once(
    "src/hooks/useScrcpy.ts",
    "        harmonyDesktop: false,\n        aspectRatioLock: true,",
    "        harmonyDesktop: false,\n        shortcutMod: 'rctrl',\n        aspectRatioLock: true,",
)
replace_once(
    "src-tauri/src/commands.rs",
    "    harmony_desktop: Option<bool>,\n    rotation: Option<String>,",
    "    harmony_desktop: Option<bool>,\n    shortcut_mod: Option<String>,\n    rotation: Option<String>,",
)
replace_once(
    "src-tauri/src/commands.rs",
    '''        if harmony_desktop {\n            args.push("--shortcut-mod=rctrl".to_string());\n        }''',
    '''        if harmony_desktop {\n            let requested = config.shortcut_mod.as_deref().unwrap_or("rctrl");\n            let shortcut_mod = match requested {\n                "lctrl" | "rctrl" | "lalt" | "ralt" | "lsuper" | "rsuper" => requested,\n                _ => "rctrl",\n            };\n            args.push(format!("--shortcut-mod={}", shortcut_mod));\n        }''',
)

# Keep the inherited advanced Harmony card accurate too.
for relative, old, new in [
    (
        "src/i18n/locales/en.ts",
        "        harmonyShortcut: 'Right Ctrl releases mouse',",
        "        harmonyShortcut: 'Mouse release shortcut is configurable',",
    ),
    (
        "src/i18n/locales/zh-CN.ts",
        "        harmonyShortcut: '右 Ctrl 释放鼠标',",
        "        harmonyShortcut: '释放鼠标快捷键可自定义',",
    ),
]:
    text = read_text(relative)
    if old in text:
        write_text(relative, text.replace(old, new, 1))


# ---------------------------------------------------------------------------
# 2) Add the release-mouse shortcut selector to the new Windows-style shell.
# ---------------------------------------------------------------------------
workspace_path = "src/components/LightWorkspace.tsx"
workspace = read_text(workspace_path)

old_input = '''                                <div className="win-divider" />\n                                <div className="win-row-section">\n                                    <div className="win-row-title">输入</div>\n                                    <div className="win-toggle-grid">\n                                        <Toggle checked={isHarmony || !!config.hidMouse} disabled={isHarmony} label="UHID 鼠标" onChange={checked => patch({ hidMouse: checked })} />\n                                        <Toggle checked={isHarmony || !!config.hidKeyboard} disabled={isHarmony} label="UHID 键盘" onChange={checked => patch({ hidKeyboard: checked })} />\n                                    </div>\n                                    {isHarmony && <span className="win-note">鸿蒙电脑模式固定使用 UHID 键鼠，并使用 Right Ctrl 作为 scrcpy 快捷修饰键。</span>}\n                                </div>'''

new_input = '''                                <div className="win-divider" />\n                                <div className="win-row-section">\n                                    <div className="win-row-title">输入</div>\n                                    <div className="win-input-controls">\n                                        <div className="win-toggle-grid">\n                                            <Toggle checked={isHarmony || !!config.hidMouse} disabled={isHarmony} label="UHID 鼠标" onChange={checked => patch({ hidMouse: checked })} />\n                                            <Toggle checked={isHarmony || !!config.hidKeyboard} disabled={isHarmony} label="UHID 键盘" onChange={checked => patch({ hidKeyboard: checked })} />\n                                        </div>\n                                        {isHarmony && (\n                                            <label className="win-field win-shortcut-field">\n                                                <span>释放鼠标快捷键</span>\n                                                <select\n                                                    className="win-select"\n                                                    value={config.shortcutMod || 'rctrl'}\n                                                    onChange={e => patch({ shortcutMod: e.target.value as ScrcpyConfig['shortcutMod'] })}\n                                                >\n                                                    <option value="rctrl">右 Ctrl</option>\n                                                    <option value="lctrl">左 Ctrl</option>\n                                                    <option value="lalt">左 Alt</option>\n                                                    <option value="ralt">右 Alt</option>\n                                                    <option value="lsuper">左 Windows</option>\n                                                    <option value="rsuper">右 Windows</option>\n                                                </select>\n                                            </label>\n                                        )}\n                                    </div>\n                                    {isHarmony && <span className="win-note">该按键同时作为 scrcpy 快捷键修饰键；按下它可切换 UHID 鼠标捕获。默认右 Ctrl。</span>}\n                                </div>'''

if workspace.count(old_input) != 1:
    raise RuntimeError("Could not locate Harmony input block in LightWorkspace.tsx")
workspace = workspace.replace(old_input, new_input, 1)
write_text(workspace_path, workspace)


# ---------------------------------------------------------------------------
# 3) Give the app an explicit viewport scroll model. The previous shell relied
#    on document scrolling, which WebView2 did not provide reliably here.
#    Main content and the device sidebar now scroll independently with wheel or
#    trackpad, while the title bar stays fixed.
# ---------------------------------------------------------------------------
css_path = "src/light-ui.css"
css = read_text(css_path)

css = '''html, body, #root {\n    height: 100%;\n    min-height: 0;\n    overflow: hidden;\n}\n\n''' + css

old_native = '''    min-height: 100vh;\n    background: var(--win-bg);'''
new_native = '''    height: 100vh;\n    min-height: 0;\n    display: flex;\n    flex-direction: column;\n    overflow: hidden;\n    background: var(--win-bg);'''
if css.count(old_native) != 1:
    raise RuntimeError("Could not locate .win-native height block")
css = css.replace(old_native, new_native, 1)

old_titlebar = '''.win-titlebar {\n    height: 54px;'''
new_titlebar = '''.win-titlebar {\n    flex: 0 0 54px;\n    height: 54px;'''
if css.count(old_titlebar) != 1:
    raise RuntimeError("Could not locate .win-titlebar block")
css = css.replace(old_titlebar, new_titlebar, 1)

old_body = ".win-body { display: grid; grid-template-columns: 248px minmax(0, 1fr); min-height: calc(100vh - 54px); }"
new_body = ".win-body { flex: 1 1 auto; min-height: 0; overflow: hidden; display: grid; grid-template-columns: 248px minmax(0, 1fr); }"
if css.count(old_body) != 1:
    raise RuntimeError("Could not locate .win-body rule")
css = css.replace(old_body, new_body, 1)

old_sidebar = ".win-sidebar { background: var(--win-surface-2); border-right: 1px solid var(--win-border); padding: 14px 12px 20px; overflow-y: auto; }"
new_sidebar = ".win-sidebar { min-height: 0; background: var(--win-surface-2); border-right: 1px solid var(--win-border); padding: 14px 12px 20px; overflow-y: auto; overscroll-behavior: contain; }"
if css.count(old_sidebar) != 1:
    raise RuntimeError("Could not locate .win-sidebar rule")
css = css.replace(old_sidebar, new_sidebar, 1)

old_content = ".win-content { padding: 22px 26px 34px; max-width: 980px; width: 100%; margin: 0 auto; }"
new_content = ".win-content { box-sizing: border-box; min-width: 0; min-height: 0; height: 100%; padding: 22px 26px 34px; max-width: 980px; width: 100%; margin: 0 auto; overflow-y: auto; overflow-x: hidden; overscroll-behavior: contain; scrollbar-gutter: stable; }"
if css.count(old_content) != 1:
    raise RuntimeError("Could not locate .win-content rule")
css = css.replace(old_content, new_content, 1)

# ---------------------------------------------------------------------------
# 4) The old ControlPanel used 7-11px micro typography. It was not actually
#    transformed, but inside the new 13px Windows shell it looked like a
#    shrunken/zoomed panel. Normalize its typography and spacing at 1:1 scale.
# ---------------------------------------------------------------------------
advanced_anchor = '''.win-native .native-advanced main { display: block; }\n.win-native .native-advanced main > * { margin-bottom: 10px; }'''
advanced_replacement = '''.win-native .native-advanced {\n    zoom: 1;\n    transform: none !important;\n    font-size: 13px;\n}\n.win-native .native-advanced main { display: block; transform: none !important; }\n.win-native .native-advanced main > * { margin-bottom: 12px; }\n.win-native .native-advanced [class*="text-[7px]"] { font-size: 11px !important; line-height: 1.35 !important; }\n.win-native .native-advanced [class*="text-[8px]"] { font-size: 11.5px !important; line-height: 1.35 !important; }\n.win-native .native-advanced [class*="text-[9px]"] { font-size: 12px !important; line-height: 1.4 !important; }\n.win-native .native-advanced [class*="text-[10px]"] { font-size: 12.5px !important; line-height: 1.4 !important; }\n.win-native .native-advanced [class*="text-[11px]"] { font-size: 13px !important; line-height: 1.4 !important; }\n.win-native .native-advanced input,\n.win-native .native-advanced button { min-height: 30px; }'''
if css.count(advanced_anchor) != 1:
    raise RuntimeError("Could not locate native advanced styling anchor")
css = css.replace(advanced_anchor, advanced_replacement, 1)

# Input layout for the new shortcut selector.
css += '''\n\n.win-input-controls {\n    display: grid;\n    grid-template-columns: minmax(0, 1fr) 210px;\n    gap: 14px 18px;\n    align-items: end;\n}\n.win-shortcut-field { margin: 0; }\n.win-shortcut-field > span { margin-bottom: 5px; }\n\n@media (max-width: 820px) {\n    .win-input-controls { grid-template-columns: 1fr; }\n}\n'''

write_text(css_path, css)

print("Light UI scrolling, advanced sizing and Harmony shortcut customization applied successfully.")
