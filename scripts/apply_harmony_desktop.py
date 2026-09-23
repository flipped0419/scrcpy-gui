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
            f"Expected exactly one match in {relative}, found {count}: {old[:160]!r}"
        )
    write_text(relative, text.replace(old, new, 1))


def insert_after_key(relative: str, key: str, insertion: str) -> None:
    text = read_text(relative)
    offset = 0
    marker = f"{key}:"
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith(marker):
            pos = offset + len(line)
            write_text(relative, text[:pos] + insertion + text[pos:])
            return
        offset += len(line)
    raise RuntimeError(f"Translation key not found in {relative}: {key}")


# 1) Persist a dedicated HarmonyOS desktop mode flag. Existing Desktop controls
# remain the source of truth for resolution, DPI, bitrate, FPS, codec and audio.
replace_once(
    "src/hooks/useScrcpy.ts",
    "    startApp?: string;\n    vdOrientation?: 'auto' | 'portrait' | 'landscape';\n    rotation?: string;",
    "    startApp?: string;\n    vdOrientation?: 'auto' | 'portrait' | 'landscape';\n    harmonyDesktop?: boolean;\n    rotation?: string;",
)
replace_once(
    "src/hooks/useScrcpy.ts",
    "        startApp: \"\",\n        vdOrientation: 'auto',\n        aspectRatioLock: true,",
    "        startApp: \"\",\n        vdOrientation: 'auto',\n        harmonyDesktop: false,\n        aspectRatioLock: true,",
)
replace_once(
    "src-tauri/src/commands.rs",
    "    start_app: Option<String>,\n    vd_orientation: Option<String>,\n    rotation: Option<String>,",
    "    start_app: Option<String>,\n    vd_orientation: Option<String>,\n    harmony_desktop: Option<bool>,\n    rotation: Option<String>,",
)


# 2) Harmony desktop uses the normal Desktop argument builder, but forces the
# input settings verified on Huawei/HarmonyOS PC mode.
replace_once(
    "src-tauri/src/commands.rs",
    '''    let otg_pure = config.otg_pure.unwrap_or(false);\n    let hid_keyboard = config.hid_keyboard.unwrap_or(false);\n    let hid_mouse = config.hid_mouse.unwrap_or(false);''',
    '''    let otg_pure = config.otg_pure.unwrap_or(false);\n    let harmony_desktop = config.session_mode == "desktop" && config.harmony_desktop.unwrap_or(false);\n    let hid_keyboard = config.hid_keyboard.unwrap_or(false) || harmony_desktop;\n    let hid_mouse = config.hid_mouse.unwrap_or(false) || harmony_desktop;''',
)
replace_once(
    "src-tauri/src/commands.rs",
    '''        if hid_mouse {\n            args.push("--mouse=uhid".to_string());\n        }\n\n        if let Some(render_driver) = &config.render_driver {''',
    '''        if hid_mouse {\n            args.push("--mouse=uhid".to_string());\n        }\n        if harmony_desktop {\n            args.push("--shortcut-mod=rctrl".to_string());\n        }\n\n        if let Some(render_driver) = &config.render_driver {''',
)

old_desktop_args = '''        } else if config.session_mode == "desktop" {\n             let mut w = config.vd_width.unwrap_or(1920);\n             let mut h = config.vd_height.unwrap_or(1080);\n             match config.vd_orientation.as_deref() {\n                 Some("portrait") if w > h => std::mem::swap(&mut w, &mut h),\n                 Some("landscape") if h > w => std::mem::swap(&mut w, &mut h),\n                 _ => {}\n             }\n             let dpi = config.vd_dpi.unwrap_or(420);\n             args.push(format!("--new-display={}x{}/{}", w, h, dpi));\n             args.push("--video-buffer=100".to_string());\n             if let Some(ref app) = config.start_app {\n                 let app = app.trim();\n                 if !app.is_empty() {\n                     args.push(format!("--start-app={}", app));\n                 }\n             }\n             // v4: flex display (resize virtual display with window)\n             if let Some(true) = config.flex_display { args.push("--flex-display".to_string()); }\n        }'''
new_desktop_args = '''        } else if config.session_mode == "desktop" {\n             let mut w = config.vd_width.unwrap_or(1920);\n             let mut h = config.vd_height.unwrap_or(1080);\n             match config.vd_orientation.as_deref() {\n                 Some("portrait") if w > h => std::mem::swap(&mut w, &mut h),\n                 Some("landscape") if h > w => std::mem::swap(&mut w, &mut h),\n                 _ => {}\n             }\n             let dpi = config.vd_dpi.unwrap_or(if harmony_desktop { 240 } else { 420 });\n             args.push(format!("--new-display={}x{}/{}", w, h, dpi));\n             args.push("--video-buffer=100".to_string());\n\n             // Huawei PC mode owns the desktop shell once CastPlusDisplay is\n             // created. App auto-launch and dynamic Flex Display are therefore\n             // intentionally kept for the ordinary virtual-display mode only.\n             if !harmony_desktop {\n                 if let Some(ref app) = config.start_app {\n                     let app = app.trim();\n                     if !app.is_empty() {\n                         args.push(format!("--start-app={}", app));\n                     }\n                 }\n                 if let Some(true) = config.flex_display {\n                     args.push("--flex-display".to_string());\n                 }\n             }\n        }'''
replace_once("src-tauri/src/commands.rs", old_desktop_args, new_desktop_args)


# 3) Select one of two server files at launch. Prefer a Harmony server next to
# the selected scrcpy executable; packaged builds also carry a bundled fallback.
replace_once(
    "src-tauri/src/commands.rs",
    '''    let exe_path = get_binary_path("scrcpy", config.scrcpy_path.clone());\n\n    // Log the session details for the user''',
    '''    let exe_path = get_binary_path("scrcpy", config.scrcpy_path.clone());\n    let harmony_desktop = config.session_mode == "desktop" && config.harmony_desktop.unwrap_or(false);\n\n    // Log the session details for the user''',
)

old_server_path = '''    let server_path = if !exe_path.is_empty() && exe_path != "scrcpy" {\n        Path::new(&exe_path).parent().map(|p| p.join("scrcpy-server").to_string_lossy().to_string())\n    } else {\n        None\n    };'''
new_server_path = '''    let server_path = if harmony_desktop {\n        let mut candidates = Vec::new();\n\n        if !exe_path.is_empty() && exe_path != "scrcpy" {\n            if let Some(parent) = Path::new(&exe_path).parent() {\n                candidates.push(parent.join("scrcpy-server-harmony"));\n            }\n        }\n\n        if let Ok(gui_exe) = std::env::current_exe() {\n            if let Some(parent) = gui_exe.parent() {\n                candidates.push(parent.join("scrcpy-server-harmony"));\n                candidates.push(parent.join("resources").join("scrcpy-server-harmony"));\n            }\n        }\n\n        if let Ok(resource_dir) = app_handle.path().resource_dir() {\n            candidates.push(resource_dir.join("scrcpy-server-harmony"));\n            candidates.push(resource_dir.join("resources").join("scrcpy-server-harmony"));\n        }\n\n        let harmony_server = candidates\n            .into_iter()\n            .find(|path| path.is_file())\n            .ok_or_else(|| {\n                "HarmonyOS desktop server not found. Expected scrcpy-server-harmony next to scrcpy or in the app resources.".to_string()\n            })?;\n\n        Some(harmony_server.to_string_lossy().to_string())\n    } else if !exe_path.is_empty() && exe_path != "scrcpy" {\n        Path::new(&exe_path).parent().map(|p| p.join("scrcpy-server").to_string_lossy().to_string())\n    } else {\n        None\n    };'''
replace_once("src-tauri/src/commands.rs", old_server_path, new_server_path)

replace_once(
    "src-tauri/src/commands.rs",
    '''    let _ = window.emit("scrcpy-log", format!("[SYSTEM] Using scrcpy: {}", exe_path));\n    let _ = window.emit("scrcpy-log", format!("[SYSTEM] Using adb: {}", adb_exe_path));''',
    '''    let _ = window.emit("scrcpy-log", format!("[SYSTEM] Using scrcpy: {}", exe_path));\n    let _ = window.emit("scrcpy-log", format!("[SYSTEM] Using adb: {}", adb_exe_path));\n    if let Some(ref sp) = server_path {\n        let label = if harmony_desktop { "HarmonyOS server" } else { "scrcpy server" };\n        let _ = window.emit("scrcpy-log", format!("[SYSTEM] Using {}: {}", label, sp));\n    }''',
)


# 4) Add a compact HarmonyOS PC Mode switch to the existing Desktop panel.
harmony_ui = '''                                <div className={`p-3 rounded-xl border transition-colors ${config.harmonyDesktop ? 'border-primary/50 bg-primary/5' : 'border-zinc-800 bg-zinc-950/30'}`}>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            const enabled = !config.harmonyDesktop;
                                            if (!enabled) {
                                                setConfig({ ...config, harmonyDesktop: false });
                                                return;
                                            }
                                            let w = config.vdWidth || 1920;
                                            let h = config.vdHeight || 1080;
                                            if (h > w) [w, h] = [h, w];
                                            const dpi = (config.vdDpi || 420) === 420 ? 240 : (config.vdDpi || 240);
                                            setConfig({
                                                ...config,
                                                harmonyDesktop: true,
                                                vdOrientation: 'landscape',
                                                vdWidth: w,
                                                vdHeight: h,
                                                vdDpi: dpi,
                                                flexDisplay: false,
                                            });
                                        }}
                                        className="w-full flex items-center justify-between gap-3 text-left"
                                    >
                                        <div className="min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className="text-[10px] font-black uppercase text-zinc-300 tracking-widest">{t('controlPanel.harmonyDesktop')}</span>
                                                <span className="text-[7px] font-black uppercase px-1.5 py-0.5 rounded border border-primary/30 text-primary bg-primary/10">{t('controlPanel.experimental')}</span>
                                            </div>
                                            <p className="mt-1 text-[8px] leading-relaxed text-zinc-500">{t('controlPanel.harmonyDesktopDescription')}</p>
                                        </div>
                                        <div className={`w-8 h-4 shrink-0 rounded-full border p-0.5 transition-colors ${config.harmonyDesktop ? 'bg-primary border-primary' : 'bg-zinc-900 border-zinc-700'}`}>
                                            <div className={`w-2.5 h-2.5 rounded-full transition-transform ${config.harmonyDesktop ? 'translate-x-3.5 bg-black' : 'translate-x-0 bg-zinc-500'}`} />
                                        </div>
                                    </button>
                                    {config.harmonyDesktop && (
                                        <div className="mt-2 pt-2 border-t border-zinc-800/60 flex flex-wrap gap-x-3 gap-y-1 text-[8px] text-zinc-500">
                                            <span>{t('controlPanel.harmonyUhid')}</span>
                                            <span>{t('controlPanel.harmonyShortcut')}</span>
                                            <span>{t('controlPanel.harmonyLimitations')}</span>
                                        </div>
                                    )}
                                </div>

'''
replace_once(
    "src/components/ControlPanel/ControlPanel.tsx",
    "                                <CustomSelect\n                                    label={t('controlPanel.displayOrientation')}",
    harmony_ui + "                                <CustomSelect\n                                    label={t('controlPanel.displayOrientation')}",
)

replace_once(
    "src/components/ControlPanel/ControlPanel.tsx",
    '''                                        <Tooltip text={t('controlPanel.flexDisplayTooltip')}>\n                                            <button\n                                                onClick={() => handleChange('flexDisplay', !config.flexDisplay)}\n                                                className={`flex items-center gap-1.5 transition-colors ${config.flexDisplay ? 'text-primary' : 'text-zinc-600 hover:text-zinc-400'}`}\n                                                title={t('controlPanel.flexDisplay')}''',
    '''                                        <Tooltip text={config.harmonyDesktop ? t('controlPanel.flexDisabledHarmony') : t('controlPanel.flexDisplayTooltip')}>\n                                            <button\n                                                onClick={() => { if (!config.harmonyDesktop) handleChange('flexDisplay', !config.flexDisplay); }}\n                                                disabled={config.harmonyDesktop}\n                                                className={`flex items-center gap-1.5 transition-colors ${config.harmonyDesktop ? 'opacity-40 cursor-not-allowed text-zinc-700' : (config.flexDisplay ? 'text-primary' : 'text-zinc-600 hover:text-zinc-400')}`}\n                                                title={config.harmonyDesktop ? t('controlPanel.flexDisabledHarmony') : t('controlPanel.flexDisplay')}''',
)


# 5) Bundle the CI-built Harmony server with Tauri installers.
tauri_path = ROOT / "src-tauri/tauri.conf.json"
tauri = json.loads(tauri_path.read_text(encoding="utf-8"))
bundle = tauri.setdefault("bundle", {})
resources = bundle.setdefault("resources", [])
if isinstance(resources, list):
    if "resources/scrcpy-server-harmony" not in resources:
        resources.append("resources/scrcpy-server-harmony")
else:
    raise RuntimeError("src-tauri/tauri.conf.json bundle.resources is not a list")
tauri_path.write_text(json.dumps(tauri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# 6) Localization. Non-Chinese locales use English fallback text for now.
insert_after_key(
    "src/i18n/locales/en.ts",
    "displayOrientation",
    "        harmonyDesktop: 'HarmonyOS PC Mode',\n"
    "        experimental: 'Experimental',\n"
    "        harmonyDesktopDescription: 'Use Huawei/HarmonyOS native PC desktop through a CastPlusDisplay virtual display. Existing resolution, DPI, bitrate, FPS, codec, audio and renderer settings are reused.',\n"
    "        harmonyUhid: 'UHID keyboard + mouse',\n"
    "        harmonyShortcut: 'Right Ctrl releases mouse',\n"
    "        harmonyLimitations: 'App launch and Flex Display are disabled in this mode',\n"
    "        flexDisabledHarmony: 'Flex Display is disabled in HarmonyOS PC Mode.',\n",
)
insert_after_key(
    "src/i18n/locales/zh-CN.ts",
    "displayOrientation",
    "        harmonyDesktop: '鸿蒙电脑模式',\n"
    "        experimental: '实验',\n"
    "        harmonyDesktopDescription: '通过 CastPlusDisplay 调用华为 / HarmonyOS 原生电脑桌面。分辨率、DPI、码率、帧率、编码、音频和渲染设置继续沿用当前桌面模式配置。',\n"
    "        harmonyUhid: 'UHID 键盘 + 鼠标',\n"
    "        harmonyShortcut: '右 Ctrl 释放鼠标',\n"
    "        harmonyLimitations: '此模式暂不使用启动应用和 Flex Display',\n"
    "        flexDisabledHarmony: '鸿蒙电脑模式下暂不启用 Flex Display。',\n",
)

fallback = (
    "        harmonyDesktop: 'HarmonyOS PC Mode',\n"
    "        experimental: 'Experimental',\n"
    "        harmonyDesktopDescription: 'Use Huawei/HarmonyOS native PC desktop through a CastPlusDisplay virtual display. Existing resolution, DPI, bitrate, FPS, codec, audio and renderer settings are reused.',\n"
    "        harmonyUhid: 'UHID keyboard + mouse',\n"
    "        harmonyShortcut: 'Right Ctrl releases mouse',\n"
    "        harmonyLimitations: 'App launch and Flex Display are disabled in this mode',\n"
    "        flexDisabledHarmony: 'Flex Display is disabled in HarmonyOS PC Mode.',\n"
)
for locale in ("fr", "pt-BR", "zh-TW", "ru", "id", "ar"):
    insert_after_key(f"src/i18n/locales/{locale}.ts", "displayOrientation", fallback)

print("HarmonyOS PC Mode customization applied successfully.")
