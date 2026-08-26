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
        raise RuntimeError(f"Expected exactly one match in {relative}, found {count}: {old[:120]!r}")
    write_text(relative, text.replace(old, new, 1))


# Classify launchable packages as user-installed vs system/preloaded. This lets
# the picker stay compact by default without hiding access to system apps.
old_command = r'''#[tauri::command]
pub async fn get_launchable_apps(device: String, custom_path: Option<String>) -> serde_json::Value {
    let adb_path = get_binary_path("adb", custom_path);
    let mut apps: Vec<String> = Vec::new();

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
                    if !package.is_empty() && package.contains('.') {
                        apps.push(package.to_string());
                    }
                }
            }
        }
    }

    // Fallback for ROMs whose `cmd package query-activities` syntax differs.
    if apps.is_empty() {
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
                            apps.push(package.to_string());
                        }
                    }
                }
            }
        }
    }

    apps.sort_by_key(|value| value.to_ascii_lowercase());
    apps.dedup();
    json!({ "success": true, "apps": apps })
}
'''

new_command = r'''#[tauri::command]
pub async fn get_launchable_apps(device: String, custom_path: Option<String>) -> serde_json::Value {
    let adb_path = get_binary_path("adb", custom_path);
    let mut apps: Vec<String> = Vec::new();
    let mut user_packages = std::collections::HashSet::<String>::new();

    // Android marks packages installed by the user with `pm list packages -3`.
    // Query it separately so a preloaded Chrome/Settings can still be shown
    // when the user switches the picker from "User" to "All".
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
                    if !package.is_empty() && package.contains('.') {
                        apps.push(package.to_string());
                    }
                }
            }
        }
    }

    // Fallback for ROMs whose `cmd package query-activities` syntax differs.
    if apps.is_empty() {
        apps.extend(user_packages.iter().cloned());
    }

    apps.sort_by_key(|value| value.to_ascii_lowercase());
    apps.dedup();
    let items: Vec<serde_json::Value> = apps
        .into_iter()
        .map(|package| {
            let is_user = user_packages.contains(&package);
            json!({ "package": package, "user": is_user })
        })
        .collect();
    json!({ "success": true, "apps": items })
}
'''
replace_once("src-tauri/src/commands.rs", old_command, new_command)

# App-picker state and filtering.
replace_once(
    "src/components/ControlPanel/ControlPanel.tsx",
    "    const [installedApps, setInstalledApps] = useState<string[]>([]);\n    const [appsLoading, setAppsLoading] = useState(false);",
    "    const [installedApps, setInstalledApps] = useState<{ package: string; user: boolean }[]>([]);\n    const [appsLoading, setAppsLoading] = useState(false);\n    const [appSearch, setAppSearch] = useState('');\n    const [appScope, setAppScope] = useState<'user' | 'all'>('user');\n    const [appPickerOpen, setAppPickerOpen] = useState(false);",
)
replace_once(
    "src/components/ControlPanel/ControlPanel.tsx",
    "    const handleChange = (field: keyof ScrcpyConfig, value: any) => {",
    '''    const filteredInstalledApps = installedApps.filter((app) => {
        if (appScope === 'user' && !app.user) return false;
        const q = appSearch.trim().toLowerCase();
        if (!q) return true;
        const friendly = app.package === 'cn.com.langeasy.LangEasyLexis' ? t('controlPanel.bbdcPreset').toLowerCase() : '';
        return app.package.toLowerCase().includes(q) || friendly.includes(q);
    });

    const handleChange = (field: keyof ScrcpyConfig, value: any) => {''',
)

old_picker = '''                                <div className="flex items-end gap-2">
                                    <CustomSelect
                                        className="flex-1 min-w-0"
                                        label={t('controlPanel.installedApps')}
                                        value={config.startApp || ""}
                                        onChange={(val) => handleChange('startApp', val)}
                                        options={[
                                            { value: "", label: t('controlPanel.appListNone') },
                                            ...installedApps.map(pkg => ({
                                                value: pkg,
                                                label: pkg === 'cn.com.langeasy.LangEasyLexis'
                                                    ? `${t('controlPanel.bbdcPreset')} · ${pkg}`
                                                    : pkg
                                            }))
                                        ]}
                                    />
                                    <button
                                        onClick={() => void refreshInstalledApps()}
                                        disabled={appsLoading || !config.device}
                                        className="h-[30px] px-2 rounded-md border border-zinc-800 bg-zinc-950 text-[8px] font-black uppercase text-primary hover:border-primary/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                                    >
                                        {appsLoading ? '...' : t('common.refresh')}
                                    </button>
                                </div>'''

new_picker = '''                                <div className="space-y-1.5">
                                    <div className="flex items-center justify-between gap-2">
                                        <label className="text-[8px] font-black text-zinc-500 uppercase tracking-widest">{t('controlPanel.installedApps')}</label>
                                        <div className="flex items-center gap-1">
                                            <button
                                                onClick={() => setAppScope('user')}
                                                className={`px-1.5 py-0.5 rounded border text-[8px] font-black transition-colors ${appScope === 'user' ? 'border-primary/50 bg-primary/10 text-primary' : 'border-zinc-800 text-zinc-600 hover:text-zinc-400'}`}
                                            >
                                                {t('controlPanel.userApps')}
                                            </button>
                                            <button
                                                onClick={() => setAppScope('all')}
                                                className={`px-1.5 py-0.5 rounded border text-[8px] font-black transition-colors ${appScope === 'all' ? 'border-primary/50 bg-primary/10 text-primary' : 'border-zinc-800 text-zinc-600 hover:text-zinc-400'}`}
                                            >
                                                {t('controlPanel.allApps')}
                                            </button>
                                            <button
                                                onClick={() => void refreshInstalledApps()}
                                                disabled={appsLoading || !config.device}
                                                className="px-1.5 py-0.5 rounded border border-zinc-800 text-[8px] font-black text-primary hover:border-primary/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                                            >
                                                {appsLoading ? '...' : t('common.refresh')}
                                            </button>
                                        </div>
                                    </div>
                                    <div className="relative">
                                        <input
                                            type="text"
                                            value={appSearch}
                                            placeholder={t('controlPanel.searchApps')}
                                            onChange={(e) => { setAppSearch(e.target.value); setAppPickerOpen(true); }}
                                            onFocus={() => setAppPickerOpen(true)}
                                            onBlur={() => window.setTimeout(() => setAppPickerOpen(false), 120)}
                                            className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1.5 text-[11px] text-zinc-300 focus:border-primary/60 focus:outline-none transition-colors"
                                        />
                                        {appPickerOpen && (
                                            <div className="absolute z-[80] left-0 right-0 mt-1 max-h-48 overflow-y-auto rounded-lg border border-zinc-800 bg-zinc-950 shadow-2xl custom-scrollbar">
                                                <button
                                                    onMouseDown={(e) => e.preventDefault()}
                                                    onClick={() => { handleChange('startApp', ''); setAppSearch(''); setAppPickerOpen(false); }}
                                                    className="w-full px-2.5 py-2 text-left text-[10px] font-bold text-zinc-500 hover:bg-zinc-900 hover:text-zinc-200 transition-colors"
                                                >
                                                    {t('controlPanel.appListNone')}
                                                </button>
                                                {filteredInstalledApps.slice(0, 100).map((app) => (
                                                    <button
                                                        key={app.package}
                                                        onMouseDown={(e) => e.preventDefault()}
                                                        onClick={() => {
                                                            handleChange('startApp', app.package);
                                                            setAppSearch(app.package === 'cn.com.langeasy.LangEasyLexis' ? t('controlPanel.bbdcPreset') : app.package);
                                                            setAppPickerOpen(false);
                                                        }}
                                                        className={`w-full px-2.5 py-2 text-left border-t border-zinc-900/80 transition-colors ${config.startApp === app.package ? 'bg-primary/10 text-primary' : 'text-zinc-300 hover:bg-zinc-900'}`}
                                                    >
                                                        <div className="text-[10px] font-bold truncate">
                                                            {app.package === 'cn.com.langeasy.LangEasyLexis' ? t('controlPanel.bbdcPreset') : app.package}
                                                        </div>
                                                        {app.package === 'cn.com.langeasy.LangEasyLexis' && (
                                                            <div className="text-[8px] text-zinc-600 font-mono truncate mt-0.5">{app.package}</div>
                                                        )}
                                                    </button>
                                                ))}
                                                {filteredInstalledApps.length === 0 && (
                                                    <div className="px-2.5 py-3 text-[9px] text-zinc-600 text-center">{t('controlPanel.noAppsFound')}</div>
                                                )}
                                                {filteredInstalledApps.length > 100 && (
                                                    <div className="sticky bottom-0 px-2.5 py-1.5 text-[8px] text-zinc-600 bg-zinc-950 border-t border-zinc-800 text-center">
                                                        {t('controlPanel.refineSearch')}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>'''
replace_once("src/components/ControlPanel/ControlPanel.tsx", old_picker, new_picker)

# Add the new picker labels to English/Chinese and typed fallback locales.
for path, marker, insertion in [
    (
        "src/i18n/locales/en.ts",
        "        installedApps: 'Installed Apps',\n",
        "        userApps: 'User',\n        allApps: 'All',\n        searchApps: 'Search apps or package name...',\n        noAppsFound: 'No matching apps',\n        refineSearch: 'More results available — refine your search',\n",
    ),
    (
        "src/i18n/locales/zh-CN.ts",
        "        installedApps: '已安装应用',\n",
        "        userApps: '用户应用',\n        allApps: '全部',\n        searchApps: '搜索应用或包名…',\n        noAppsFound: '没有匹配的应用',\n        refineSearch: '结果较多，请继续输入关键词',\n",
    ),
]:
    replace_once(path, marker, marker + insertion)

fallback = (
    "        userApps: 'User',\n"
    "        allApps: 'All',\n"
    "        searchApps: 'Search apps or package name...',\n"
    "        noAppsFound: 'No matching apps',\n"
    "        refineSearch: 'More results available — refine your search',\n"
)
for locale in ("fr", "pt-BR", "zh-TW", "ru", "id", "ar"):
    path = f"src/i18n/locales/{locale}.ts"
    text = read_text(path)
    marker = "        installedApps: 'Installed Apps',\n"
    if marker not in text:
        # Some locale files use a different indent width; match by stripped line.
        lines = text.splitlines(keepends=True)
        offset = 0
        for line in lines:
            if line.lstrip().startswith("installedApps:"):
                pos = offset + len(line)
                write_text(path, text[:pos] + fallback + text[pos:])
                break
            offset += len(line)
        else:
            raise RuntimeError(f"installedApps key not found in {path}")
    else:
        replace_once(path, marker, marker + fallback)

print("Searchable bounded app picker applied successfully.")
