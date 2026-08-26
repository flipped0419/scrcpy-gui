from __future__ import annotations

import json
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
            f"Expected exactly one match in {relative}, found {count}: {old[:80]!r}"
        )
    write_text(relative, text.replace(old, new, 1))


def insert_before_in_section(relative: str, section_marker: str, target: str, insertion: str) -> None:
    text = read_text(relative)
    section_pos = text.find(section_marker)
    if section_pos < 0:
        raise RuntimeError(f"Section marker not found in {relative}: {section_marker!r}")
    target_pos = text.find(target, section_pos)
    if target_pos < 0:
        raise RuntimeError(f"Target not found after section marker in {relative}: {target!r}")
    write_text(relative, text[:target_pos] + insertion + text[target_pos:])


# 1) Let the main Tauri window resize and enable WebView zoom hotkeys.
tauri_path = ROOT / "src-tauri/tauri.conf.json"
tauri = json.loads(tauri_path.read_text(encoding="utf-8"))
main_window = next(w for w in tauri["app"]["windows"] if w.get("label") == "main")
main_window["resizable"] = True
main_window["zoomHotkeysEnabled"] = True
tauri_path.write_text(json.dumps(tauri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 2) Add an optional startApp field to the frontend config and persist it with the
#    existing scrcpy_config localStorage mechanism.
replace_once(
    "src/hooks/useScrcpy.ts",
    "    vdDpi?: number;\n    rotation?: string;",
    "    vdDpi?: number;\n    startApp?: string;\n    rotation?: string;",
)
replace_once(
    "src/hooks/useScrcpy.ts",
    "        vdDpi: 420,\n        aspectRatioLock: true,",
    "        vdDpi: 420,\n        startApp: \"\",\n        aspectRatioLock: true,",
)

# 3) Thread startApp through the Rust config and translate it to scrcpy's
#    --start-app=<package> whenever Desktop/Virtual Display mode is used.
replace_once(
    "src-tauri/src/commands.rs",
    "    vd_dpi: Option<u32>,\n    rotation: Option<String>,",
    "    vd_dpi: Option<u32>,\n    start_app: Option<String>,\n    rotation: Option<String>,",
)
replace_once(
    "src-tauri/src/commands.rs",
    "             args.push(format!(\"--new-display={}x{}/{}\", w, h, dpi));\n             args.push(\"--video-buffer=100\".to_string());\n             // v4: flex display (resize virtual display with window)\n             if let Some(true) = config.flex_display { args.push(\"--flex-display\".to_string()); }",
    "             args.push(format!(\"--new-display={}x{}/{}\", w, h, dpi));\n             args.push(\"--video-buffer=100\".to_string());\n             if let Some(ref app) = config.start_app {\n                 let app = app.trim();\n                 if !app.is_empty() {\n                     args.push(format!(\"--start-app={}\", app));\n                 }\n             }\n             // v4: flex display (resize virtual display with window)\n             if let Some(true) = config.flex_display { args.push(\"--flex-display\".to_string()); }",
)

# 4) Add a compact Launch App card to the existing Desktop mode. The BBDC
#    shortcut fills the package name once; config persistence remembers it.
launch_app_ui = '''                            <div className="p-3 rounded-xl border border-zinc-800 bg-zinc-950/30 space-y-2">
                                <div className="flex items-center justify-between gap-2">
                                    <div className="flex items-center gap-1.5">
                                        <label className="text-[9px] font-black text-zinc-500 uppercase tracking-tighter">{t('controlPanel.startApp')}</label>
                                        <Tooltip text={t('controlPanel.startAppHint')} placement="top" />
                                    </div>
                                    <button
                                        onClick={() => handleChange('startApp', 'cn.com.langeasy.LangEasyLexis')}
                                        className="text-[8px] font-black uppercase text-primary hover:text-white transition-colors"
                                    >
                                        {t('controlPanel.bbdcPreset')}
                                    </button>
                                </div>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="text"
                                        placeholder="com.example.app"
                                        value={config.startApp || ''}
                                        onChange={(e) => handleChange('startApp', e.target.value)}
                                        className="flex-1 bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1.5 text-[11px] text-zinc-300 focus:border-primary/60 focus:outline-none transition-colors font-mono"
                                    />
                                    {config.startApp && (
                                        <button
                                            onClick={() => handleChange('startApp', '')}
                                            className="text-[8px] font-black text-zinc-600 hover:text-red-400 uppercase transition-colors"
                                        >
                                            {t('common.clear')}
                                        </button>
                                    )}
                                </div>
                                <p className="text-[8px] text-zinc-600 leading-relaxed">{t('controlPanel.startAppDescription')}</p>
                            </div>

'''
insert_before_in_section(
    "src/components/ControlPanel/ControlPanel.tsx",
    "                    {/* Desktop Config */}",
    "                            <div className=\"space-y-2.5 pt-0.5\">",
    launch_app_ui,
)

# 5) Add English fallback plus Simplified Chinese strings. Other locales use
#    the existing deep-merge fallback to English.
replace_once(
    "src/i18n/locales/en.ts",
    "        backgroundColorNone: 'Default',\n        badgeNew: 'NEW',",
    "        backgroundColorNone: 'Default',\n        startApp: 'Launch App',\n        startAppHint: 'Start an Android app directly on the virtual display.',\n        startAppDescription: 'Optional package name. Leave blank for the normal virtual desktop. The value is remembered automatically.',\n        bbdcPreset: 'BBDC',\n        badgeNew: 'NEW',",
)
replace_once(
    "src/i18n/locales/zh-CN.ts",
    "        backgroundColorNone: '默认',\n        badgeNew: '新',",
    "        backgroundColorNone: '默认',\n        startApp: '启动应用',\n        startAppHint: '在虚拟显示器上直接启动指定 Android 应用。',\n        startAppDescription: '可选。填写应用包名；留空则保持普通虚拟桌面。设置会自动记住。',\n        bbdcPreset: '不背单词',\n        badgeNew: '新',",
)

print("Fork customizations applied successfully.")
