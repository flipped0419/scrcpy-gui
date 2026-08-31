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
        raise RuntimeError(f"Expected exactly one match in {relative}, found {count}: {old[:140]!r}")
    write_text(relative, text.replace(old, new, 1))


def replace_between(relative: str, start: str, end: str, replacement: str) -> None:
    text = read_text(relative)
    start_pos = text.find(start)
    if start_pos < 0:
        raise RuntimeError(f"Start marker not found in {relative}: {start!r}")
    end_pos = text.find(end, start_pos)
    if end_pos < 0:
        raise RuntimeError(f"End marker not found in {relative}: {end!r}")
    write_text(relative, text[:start_pos] + replacement + text[end_pos:])


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


# ---------------------------------------------------------------------------
# 1) Read real application labels from scrcpy --list-apps.
#    Keep the ADB launcher query as the source of truth for launchability, then
#    intersect scrcpy's richer app metadata with that launcher package set.
# ---------------------------------------------------------------------------
new_get_launchable_apps = r'''#[tauri::command]
pub async fn get_launchable_apps(device: String, custom_path: Option<String>) -> serde_json::Value {
    let adb_path = get_binary_path("adb", custom_path.clone());
    let scrcpy_path = get_binary_path("scrcpy", custom_path);
    let mut apps: Vec<String> = Vec::new();
    let mut user_packages = std::collections::HashSet::<String>::new();

    if let Ok(output) = create_command(&adb_path)
        .arg("-s")
        .arg(&device)
        .args(["shell", "pm", "list", "packages", "-3"])
        .output()
        .await
    {
        if output.status.success() {
            let text = String::from_utf8_lossy(&output.stdout);
            for line in text.lines() {
                if let Some(package) = line.trim().strip_prefix("package:") {
                    let package = package.trim();
                    if !package.is_empty() {
                        user_packages.insert(package.to_string());
                    }
                }
            }
        }
    }

    let launcher_query = create_command(&adb_path)
        .arg("-s")
        .arg(&device)
        .args([
            "shell",
            "cmd",
            "package",
            "query-activities",
            "--brief",
            "-a",
            "android.intent.action.MAIN",
            "-c",
            "android.intent.category.LAUNCHER",
        ])
        .output()
        .await;

    if let Ok(output) = launcher_query {
        if output.status.success() {
            let text = String::from_utf8_lossy(&output.stdout);
            for line in text.lines() {
                let line = line.trim();
                if let Some((package, _activity)) = line.split_once('/') {
                    let package = package.trim();
                    if !package.is_empty() {
                        apps.push(package.to_string());
                    }
                }
            }
        }
    }

    // Vendor-ROM fallback: at least keep user-installed packages selectable.
    if apps.is_empty() {
        apps.extend(user_packages.iter().cloned());
    }

    apps.sort_by_key(|value| value.to_ascii_lowercase());
    apps.dedup();
    let launchable = apps.iter().cloned().collect::<std::collections::HashSet<_>>();
    let mut app_names = std::collections::HashMap::<String, String>::new();

    // scrcpy's server resolves localized application labels using Android's own
    // PackageManager. It may take a few seconds on devices with many apps, so
    // this is done only when the Desktop app picker is refreshed/opened.
    if let Ok(output) = create_command(&scrcpy_path)
        .arg("-s")
        .arg(&device)
        .arg("--list-apps")
        .output()
        .await
    {
        let combined = format!(
            "{}\n{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
        let mut pending_name: Option<String> = None;

        for raw in combined.lines() {
            let mut line = raw.trim();
            // scrcpy server logs normally prefix only the first line, but some
            // environments may repeat the log prefix on every line.
            if let Some(pos) = line.find("INFO: ") {
                line = &line[(pos + 6)..];
            }

            let marked = line
                .strip_prefix("* ")
                .or_else(|| line.strip_prefix("- "));

            if let Some(rest) = marked {
                let rest = rest.trim_end();
                let mut matched_package: Option<&String> = None;
                for package in &launchable {
                    if rest == package || (rest.ends_with(package.as_str()) && rest[..rest.len() - package.len()].ends_with(char::is_whitespace)) {
                        matched_package = Some(package);
                        break;
                    }
                }

                if let Some(package) = matched_package {
                    let name = rest[..rest.len() - package.len()].trim();
                    if !name.is_empty() {
                        app_names.insert(package.clone(), name.to_string());
                    }
                    pending_name = None;
                } else if !rest.is_empty() {
                    // Long names are wrapped by scrcpy: the package appears on
                    // the following indented line.
                    pending_name = Some(rest.trim().to_string());
                }
                continue;
            }

            if let Some(name) = pending_name.take() {
                let package = line.trim();
                if launchable.contains(package) {
                    app_names.insert(package.to_string(), name);
                }
            }
        }
    }

    let mut items: Vec<serde_json::Value> = apps
        .into_iter()
        .map(|package| {
            let is_user = user_packages.contains(&package);
            let name = app_names
                .get(&package)
                .cloned()
                .unwrap_or_else(|| package.clone());
            json!({ "package": package, "name": name, "user": is_user })
        })
        .collect();

    items.sort_by(|a, b| {
        let an = a.get("name").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
        let bn = b.get("name").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
        an.cmp(&bn)
    });

    json!({ "success": true, "apps": items })
}

'''
replace_between(
    "src-tauri/src/commands.rs",
    "#[tauri::command]\npub async fn get_launchable_apps(device: String, custom_path: Option<String>) -> serde_json::Value {",
    "#[tauri::command]\npub async fn get_mdns_devices(custom_path: Option<String>) -> serde_json::Value {",
    new_get_launchable_apps,
)


# ---------------------------------------------------------------------------
# 2) Persist a virtual-display orientation preference and enforce it when
#    building --new-display. This changes the *virtual display aspect*, not the
#    app's internal orientation policy; portrait-only apps therefore get a
#    portrait canvas instead of being letterboxed on a landscape canvas.
# ---------------------------------------------------------------------------
replace_once(
    "src/hooks/useScrcpy.ts",
    "    vdDpi?: number;\n    startApp?: string;\n    rotation?: string;",
    "    vdDpi?: number;\n    startApp?: string;\n    vdOrientation?: 'auto' | 'portrait' | 'landscape';\n    rotation?: string;",
)
replace_once(
    "src/hooks/useScrcpy.ts",
    "        vdDpi: 420,\n        startApp: \"\",\n        aspectRatioLock: true,",
    "        vdDpi: 420,\n        startApp: \"\",\n        vdOrientation: 'auto',\n        aspectRatioLock: true,",
)
replace_once(
    "src-tauri/src/commands.rs",
    "    vd_dpi: Option<u32>,\n    start_app: Option<String>,\n    rotation: Option<String>,",
    "    vd_dpi: Option<u32>,\n    start_app: Option<String>,\n    vd_orientation: Option<String>,\n    rotation: Option<String>,",
)

old_desktop_args = '''        } else if config.session_mode == "desktop" {
             let w = config.vd_width.unwrap_or(1920);
             let h = config.vd_height.unwrap_or(1080);
             let dpi = config.vd_dpi.unwrap_or(420);
             args.push(format!("--new-display={}x{}/{}", w, h, dpi));
             args.push("--video-buffer=100".to_string());
             if let Some(ref app) = config.start_app {
                 let app = app.trim();
                 if !app.is_empty() {
                     args.push(format!("--start-app={}", app));
                 }
             }
             // v4: flex display (resize virtual display with window)
             if let Some(true) = config.flex_display { args.push("--flex-display".to_string()); }
        }'''
new_desktop_args = '''        } else if config.session_mode == "desktop" {
             let mut w = config.vd_width.unwrap_or(1920);
             let mut h = config.vd_height.unwrap_or(1080);
             match config.vd_orientation.as_deref() {
                 Some("portrait") if w > h => std::mem::swap(&mut w, &mut h),
                 Some("landscape") if h > w => std::mem::swap(&mut w, &mut h),
                 _ => {}
             }
             let dpi = config.vd_dpi.unwrap_or(420);
             args.push(format!("--new-display={}x{}/{}", w, h, dpi));
             args.push("--video-buffer=100".to_string());
             if let Some(ref app) = config.start_app {
                 let app = app.trim();
                 if !app.is_empty() {
                     args.push(format!("--start-app={}", app));
                 }
             }
             // v4: flex display (resize virtual display with window)
             if let Some(true) = config.flex_display { args.push("--flex-display".to_string()); }
        }'''
replace_once("src-tauri/src/commands.rs", old_desktop_args, new_desktop_args)


# ---------------------------------------------------------------------------
# 3) Show real app names in the picker (package as secondary text) and search
#    both fields. Also keep the search box synchronized with the chosen app.
# ---------------------------------------------------------------------------
replace_once(
    "src/components/ControlPanel/ControlPanel.tsx",
    "    const [installedApps, setInstalledApps] = useState<{ package: string; user: boolean }[]>([]);",
    "    const [installedApps, setInstalledApps] = useState<{ package: string; name: string; user: boolean }[]>([]);",
)

old_filter = '''    const filteredInstalledApps = installedApps.filter((app) => {
        if (appScope === 'user' && !app.user) return false;
        const q = appSearch.trim().toLowerCase();
        if (!q) return true;
        const friendly = app.package === 'cn.com.langeasy.LangEasyLexis' ? t('controlPanel.bbdcPreset').toLowerCase() : '';
        return app.package.toLowerCase().includes(q) || friendly.includes(q);
    });'''
new_filter = '''    const filteredInstalledApps = installedApps.filter((app) => {
        if (appScope === 'user' && !app.user) return false;
        const q = appSearch.trim().toLowerCase();
        if (!q) return true;
        return app.package.toLowerCase().includes(q) || (app.name || '').toLowerCase().includes(q);
    });

    useEffect(() => {
        if (!config.startApp || appPickerOpen) return;
        const selected = installedApps.find(app => app.package === config.startApp);
        if (selected) setAppSearch(selected.name || selected.package);
    }, [installedApps, config.startApp, appPickerOpen]);'''
replace_once("src/components/ControlPanel/ControlPanel.tsx", old_filter, new_filter)

old_selection = '''                                                        onClick={() => {
                                                            handleChange('startApp', app.package);
                                                            setAppSearch(app.package === 'cn.com.langeasy.LangEasyLexis' ? t('controlPanel.bbdcPreset') : app.package);
                                                            setAppPickerOpen(false);
                                                        }}'''
new_selection = '''                                                        onClick={() => {
                                                            const isBbdc = app.package === 'cn.com.langeasy.LangEasyLexis';
                                                            if (isBbdc) {
                                                                const w = config.vdWidth || 1920;
                                                                const h = config.vdHeight || 1080;
                                                                setConfig({
                                                                    ...config,
                                                                    startApp: app.package,
                                                                    vdOrientation: 'portrait',
                                                                    vdWidth: Math.min(w, h),
                                                                    vdHeight: Math.max(w, h),
                                                                });
                                                            } else {
                                                                handleChange('startApp', app.package);
                                                            }
                                                            setAppSearch(app.name || app.package);
                                                            setAppPickerOpen(false);
                                                        }}'''
replace_once("src/components/ControlPanel/ControlPanel.tsx", old_selection, new_selection)

old_app_row = '''                                                        <div className="text-[10px] font-bold truncate">
                                                            {app.package === 'cn.com.langeasy.LangEasyLexis' ? t('controlPanel.bbdcPreset') : app.package}
                                                        </div>
                                                        {app.package === 'cn.com.langeasy.LangEasyLexis' && (
                                                            <div className="text-[8px] text-zinc-600 font-mono truncate mt-0.5">{app.package}</div>
                                                        )}'''
new_app_row = '''                                                        <div className="flex items-center gap-2 min-w-0">
                                                            <div className="w-6 h-6 shrink-0 rounded-md border border-zinc-800 bg-zinc-900 flex items-center justify-center text-[10px] font-black text-primary">
                                                                {(app.name || app.package).trim().charAt(0).toUpperCase() || 'A'}
                                                            </div>
                                                            <div className="min-w-0 flex-1">
                                                                <div className="text-[10px] font-bold truncate">{app.name || app.package}</div>
                                                                <div className="text-[8px] text-zinc-600 font-mono truncate mt-0.5">{app.package}</div>
                                                            </div>
                                                        </div>'''
replace_once("src/components/ControlPanel/ControlPanel.tsx", old_app_row, new_app_row)

# BBDC shortcut button also selects the portrait virtual-display preset.
replace_once(
    "src/components/ControlPanel/ControlPanel.tsx",
    "                                        onClick={() => handleChange('startApp', 'cn.com.langeasy.LangEasyLexis')}",
    "                                        onClick={() => {\n                                            const w = config.vdWidth || 1920;\n                                            const h = config.vdHeight || 1080;\n                                            setConfig({ ...config, startApp: 'cn.com.langeasy.LangEasyLexis', vdOrientation: 'portrait', vdWidth: Math.min(w, h), vdHeight: Math.max(w, h) });\n                                            setAppSearch(t('controlPanel.bbdcPreset'));\n                                        }}",
)


# ---------------------------------------------------------------------------
# 4) Add Auto / Portrait / Landscape control to the virtual-display card.
# ---------------------------------------------------------------------------
orientation_ui = '''                                <CustomSelect
                                    label={t('controlPanel.displayOrientation')}
                                    value={config.vdOrientation || 'auto'}
                                    onChange={(val: 'auto' | 'portrait' | 'landscape') => {
                                        let w = config.vdWidth || 1920;
                                        let h = config.vdHeight || 1080;
                                        if (val === 'portrait' && w > h) [w, h] = [h, w];
                                        if (val === 'landscape' && h > w) [w, h] = [h, w];
                                        setConfig({ ...config, vdOrientation: val, vdWidth: w, vdHeight: h });
                                    }}
                                    options={[
                                        { value: 'auto', label: t('controlPanel.orientationAuto') },
                                        { value: 'portrait', label: t('controlPanel.orientationPortrait') },
                                        { value: 'landscape', label: t('controlPanel.orientationLandscape') },
                                    ]}
                                />

'''
replace_once(
    "src/components/ControlPanel/ControlPanel.tsx",
    "                                <div className=\"grid grid-cols-2 gap-x-4 gap-y-3\">",
    orientation_ui + "                                <div className=\"grid grid-cols-2 gap-x-4 gap-y-3\">",
)

# Keep quick presets consistent with the selected orientation.
old_presets = '''                                        onChange={(val: string) => {
                                            if (val === '1080p') setConfig({ ...config, vdWidth: 1920, vdHeight: 1080 });
                                            if (val === '1440p') setConfig({ ...config, vdWidth: 2560, vdHeight: 1440 });
                                            if (val === '4k') setConfig({ ...config, vdWidth: 3840, vdHeight: 2160 });
                                            if (val === 'ultrawide') setConfig({ ...config, vdWidth: 2560, vdHeight: 1080 });
                                        }}'''
new_presets = '''                                        onChange={(val: string) => {
                                            let w = 1920;
                                            let h = 1080;
                                            if (val === '1440p') [w, h] = [2560, 1440];
                                            if (val === '4k') [w, h] = [3840, 2160];
                                            if (val === 'ultrawide') [w, h] = [2560, 1080];
                                            if (config.vdOrientation === 'portrait' && w > h) [w, h] = [h, w];
                                            if (config.vdOrientation === 'landscape' && h > w) [w, h] = [h, w];
                                            setConfig({ ...config, vdWidth: w, vdHeight: h });
                                        }}'''
replace_once("src/components/ControlPanel/ControlPanel.tsx", old_presets, new_presets)


# ---------------------------------------------------------------------------
# 5) Localization. Other typed locales use English text for the new controls.
# ---------------------------------------------------------------------------
insert_after_key(
    "src/i18n/locales/en.ts",
    "installedApps",
    "        displayOrientation: 'Display Orientation',\n"
    "        orientationAuto: 'Auto / use dimensions',\n"
    "        orientationPortrait: 'Portrait',\n"
    "        orientationLandscape: 'Landscape',\n",
)
insert_after_key(
    "src/i18n/locales/zh-CN.ts",
    "installedApps",
    "        displayOrientation: '显示方向',\n"
    "        orientationAuto: '自动 / 按当前尺寸',\n"
    "        orientationPortrait: '竖屏',\n"
    "        orientationLandscape: '横屏',\n",
)

fallback = (
    "        displayOrientation: 'Display Orientation',\n"
    "        orientationAuto: 'Auto / use dimensions',\n"
    "        orientationPortrait: 'Portrait',\n"
    "        orientationLandscape: 'Landscape',\n"
)
for locale in ("fr", "pt-BR", "zh-TW", "ru", "id", "ar"):
    insert_after_key(f"src/i18n/locales/{locale}.ts", "installedApps", fallback)

print("Real app names + virtual-display orientation presets applied successfully.")
