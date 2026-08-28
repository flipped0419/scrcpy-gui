from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write_text(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


LIGHT_WORKSPACE = r'''import type { Dispatch, SetStateAction } from 'react';
import type { MdnsDevice, RenderDriverSupport, ScrcpyConfig } from '../hooks/useScrcpy';
import Sidebar from './Sidebar';
import ControlPanel from './ControlPanel';
import LogPanel from './LogPanel';
import ShortcutsPanel from './ShortcutsPanel';

interface LightWorkspaceProps {
    config: ScrcpyConfig;
    setConfig: Dispatch<SetStateAction<ScrcpyConfig>>;
    onStart: () => void;
    onStop: () => void;
    isRunning: boolean;
    devices: string[];
    deviceModels: Record<string, string>;
    deviceFriendlyNames: Record<string, string>;
    runningDevices: string[];
    onRefresh: () => void;
    onKillAdb: () => void;
    selectedDevice: string;
    onSelectDevice: (device: string) => void;
    onPair: (...args: any[]) => any;
    onConnect: (...args: any[]) => any;
    isRefreshing: boolean;
    onFilePush: () => void;
    historyDevices: string[];
    clearHistory: () => void;
    mdnsDevices: MdnsDevice[];
    logs: string[];
    onClearLogs: () => void;
    onAddLog: (message: string) => void;
    onRunCommand: (...args: any[]) => any;
    detectedCameras: { id: string; name: string }[];
    renderDriverSupport: RenderDriverSupport;
    onListOptions: (arg: string) => void;
    binaryStatus: { found: boolean; message: string };
    onDownload: () => void;
    onSetPath: () => void;
    onResetPath: () => void;
    isDownloading: boolean;
    downloadProgress: number;
    version: string;
    colorMode: 'light' | 'dark' | 'system';
    onColorModeChange: (mode: 'light' | 'dark' | 'system') => void;
}

type Mode = 'mirror' | 'desktop' | 'harmony' | 'camera';

const desktopPresets = [
    ['1920x1080', '1920 × 1080'],
    ['2560x1440', '2560 × 1440'],
    ['3840x2160', '3840 × 2160'],
    ['2560x1080', '2560 × 1080'],
];

const mirrorResolutions = [
    ['0', '原始'],
    ['3840', '4K'],
    ['2560', '2K'],
    ['1920', '1080p'],
    ['1600', '900p'],
    ['1280', '720p'],
    ['1024', '576p'],
    ['800', '480p'],
];

function Toggle({ checked, disabled = false, label, onChange }: { checked: boolean; disabled?: boolean; label: string; onChange: (checked: boolean) => void }) {
    return (
        <label className={`win-toggle ${disabled ? 'is-disabled' : ''}`}>
            <input type="checkbox" checked={checked} disabled={disabled} onChange={e => onChange(e.target.checked)} />
            <span>{label}</span>
        </label>
    );
}

export default function LightWorkspace(props: LightWorkspaceProps) {
    const {
        config, setConfig, onStart, onStop, isRunning,
        devices, deviceModels, deviceFriendlyNames, runningDevices,
        onRefresh, onKillAdb, selectedDevice, onSelectDevice, onPair, onConnect,
        isRefreshing, onFilePush, historyDevices, clearHistory, mdnsDevices,
        logs, onClearLogs, onAddLog, onRunCommand, detectedCameras,
        renderDriverSupport, onListOptions, binaryStatus, onDownload, onSetPath,
        onResetPath, isDownloading, downloadProgress, version, colorMode, onColorModeChange,
    } = props;

    const patch = (values: Partial<ScrcpyConfig>) => setConfig(prev => ({ ...prev, ...values }));
    const mode: Mode = config.sessionMode === 'desktop'
        ? (config.harmonyDesktop ? 'harmony' : 'desktop')
        : (config.sessionMode as Mode);
    const isHarmony = mode === 'harmony';
    const isDesktop = mode === 'desktop' || isHarmony;
    const isCamera = mode === 'camera';

    const selectedName = selectedDevice
        ? (deviceFriendlyNames[selectedDevice] || deviceModels[selectedDevice] || selectedDevice)
        : '未选择设备';

    const setMode = (next: Mode) => {
        if (next === 'harmony') {
            let width = config.vdWidth || 1920;
            let height = config.vdHeight || 1080;
            if (height > width) [width, height] = [height, width];
            patch({
                sessionMode: 'desktop',
                harmonyDesktop: true,
                vdOrientation: 'landscape',
                vdWidth: width,
                vdHeight: height,
                vdDpi: (config.vdDpi || 420) === 420 ? 240 : (config.vdDpi || 240),
                flexDisplay: false,
            });
            return;
        }
        patch({ sessionMode: next, harmonyDesktop: false });
    };

    const desktopResolution = `${config.vdWidth || 1920}x${config.vdHeight || 1080}`;
    const knownDesktopPreset = desktopPresets.some(([value]) => value === desktopResolution);

    return (
        <div className="win-native">
            <header className="win-titlebar">
                <div className="win-brand">
                    <div className="win-app-icon">S</div>
                    <div>
                        <strong>ScrcpyGUI</strong>
                        <span>v{version}</span>
                    </div>
                </div>
                <div className="win-device-status">
                    <span className={`win-status-dot ${selectedDevice ? 'online' : ''}`} />
                    <span className="win-device-name">{selectedName}</span>
                    <span className="win-connection-state">{selectedDevice ? '已连接' : '未连接'}</span>
                </div>
                <div className="win-title-actions">
                    {isDownloading && <span className="win-download-progress">下载 {Math.round(downloadProgress)}%</span>}
                    <button className="win-button subtle" onClick={binaryStatus.found ? onSetPath : onDownload}>
                        {binaryStatus.found ? 'Scrcpy 路径' : '安装 Scrcpy'}
                    </button>
                    {binaryStatus.found && <button className="win-button ghost" onClick={onResetPath}>默认路径</button>}
                    <select className="win-select compact" value={colorMode} onChange={e => onColorModeChange(e.target.value as 'light' | 'dark' | 'system')}>
                        <option value="system">跟随系统</option>
                        <option value="light">浅色</option>
                        <option value="dark">深色</option>
                    </select>
                </div>
            </header>

            <div className="win-body">
                <aside className="win-sidebar">
                    <div className="win-section-title">设备</div>
                    <Sidebar
                        devices={devices}
                        deviceModels={deviceModels}
                        deviceFriendlyNames={deviceFriendlyNames}
                        runningDevices={runningDevices}
                        onRefresh={onRefresh}
                        onKillAdb={onKillAdb}
                        selectedDevice={selectedDevice}
                        onSelectDevice={onSelectDevice}
                        onPair={onPair}
                        onConnect={onConnect}
                        isRefreshing={isRefreshing}
                        onFilePush={onFilePush}
                        historyDevices={historyDevices}
                        clearHistory={clearHistory}
                        mdnsDevices={mdnsDevices}
                    />
                </aside>

                <main className="win-content">
                    <section className="win-panel win-primary-panel">
                        <div className="win-section-heading">
                            <div>
                                <h1>投屏设置</h1>
                                <p>常用参数集中在这里，高级选项默认收起。</p>
                            </div>
                            <div className="win-binary-state">{binaryStatus.found ? 'Scrcpy 已就绪' : binaryStatus.message}</div>
                        </div>

                        <div className="win-field-group">
                            <label className="win-label">模式</label>
                            <div className="win-segmented four">
                                <button className={mode === 'mirror' ? 'active' : ''} onClick={() => setMode('mirror')}>手机屏幕</button>
                                <button className={mode === 'desktop' ? 'active' : ''} onClick={() => setMode('desktop')}>虚拟桌面</button>
                                <button className={mode === 'harmony' ? 'active' : ''} onClick={() => setMode('harmony')}>鸿蒙电脑模式</button>
                                <button className={mode === 'camera' ? 'active' : ''} onClick={() => setMode('camera')}>摄像头</button>
                            </div>
                        </div>

                        {!isCamera && (
                            <>
                                <div className="win-settings-grid">
                                    {isDesktop ? (
                                        <>
                                            <label className="win-field">
                                                <span>分辨率</span>
                                                <select className="win-select" value={knownDesktopPreset ? desktopResolution : 'custom'} onChange={e => {
                                                    if (e.target.value === 'custom') return;
                                                    const [w, h] = e.target.value.split('x').map(Number);
                                                    patch({ vdWidth: w, vdHeight: h });
                                                }}>
                                                    {desktopPresets.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                                                    {!knownDesktopPreset && <option value="custom">{config.vdWidth} × {config.vdHeight}</option>}
                                                </select>
                                            </label>
                                            <label className="win-field">
                                                <span>DPI</span>
                                                <input className="win-input" type="number" min={120} max={640} step={10} value={config.vdDpi || (isHarmony ? 240 : 420)} onChange={e => patch({ vdDpi: Number(e.target.value) || 240 })} />
                                            </label>
                                        </>
                                    ) : (
                                        <label className="win-field">
                                            <span>分辨率</span>
                                            <select className="win-select" value={config.res || '0'} onChange={e => patch({ res: e.target.value })}>
                                                {mirrorResolutions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                                            </select>
                                        </label>
                                    )}
                                    <label className="win-field">
                                        <span>帧率</span>
                                        <select className="win-select" value={config.fps || 0} onChange={e => patch({ fps: Number(e.target.value) || undefined })}>
                                            <option value={0}>自动</option>
                                            <option value={30}>30 FPS</option>
                                            <option value={60}>60 FPS</option>
                                            <option value={90}>90 FPS</option>
                                            <option value={120}>120 FPS</option>
                                        </select>
                                    </label>
                                    <label className="win-field">
                                        <span>码率</span>
                                        <div className="win-inline-input"><input className="win-input" type="number" min={1} max={50} value={config.bitrate || 8} onChange={e => patch({ bitrate: Number(e.target.value) || 8 })} /><span>Mbps</span></div>
                                    </label>
                                    <label className="win-field">
                                        <span>编码</span>
                                        <select className="win-select" value={config.codec || 'h264'} onChange={e => patch({ codec: e.target.value })}>
                                            <option value="h264">H.264</option>
                                            <option value="h265">H.265 / HEVC</option>
                                            <option value="av1">AV1</option>
                                            <option value="vp9">VP9</option>
                                        </select>
                                    </label>
                                </div>

                                <div className="win-divider" />
                                <div className="win-row-section">
                                    <div className="win-row-title">输入</div>
                                    <div className="win-toggle-grid">
                                        <Toggle checked={isHarmony || !!config.hidMouse} disabled={isHarmony} label="UHID 鼠标" onChange={checked => patch({ hidMouse: checked })} />
                                        <Toggle checked={isHarmony || !!config.hidKeyboard} disabled={isHarmony} label="UHID 键盘" onChange={checked => patch({ hidKeyboard: checked })} />
                                    </div>
                                    {isHarmony && <span className="win-note">鸿蒙电脑模式固定使用 UHID 键鼠，并使用 Right Ctrl 作为 scrcpy 快捷修饰键。</span>}
                                </div>

                                <div className="win-divider" />
                                <div className="win-row-section">
                                    <div className="win-row-title">行为</div>
                                    <div className="win-toggle-grid behavior">
                                        <Toggle checked={!!config.turnOff} label="熄灭手机主屏" onChange={checked => patch({ turnOff: checked })} />
                                        <Toggle checked={!!config.stayAwake} label="保持唤醒" onChange={checked => patch({ stayAwake: checked })} />
                                        <Toggle checked={config.audioEnabled !== false} label="转发音频" onChange={checked => patch({ audioEnabled: checked })} />
                                        <Toggle checked={!!config.keepActive} label="保持活跃" onChange={checked => patch({ keepActive: checked })} />
                                        <Toggle checked={!!config.alwaysOnTop} label="窗口置顶" onChange={checked => patch({ alwaysOnTop: checked })} />
                                        <Toggle checked={!!config.fullscreen} label="全屏" onChange={checked => patch({ fullscreen: checked })} />
                                        <Toggle checked={!!config.borderless} label="无边框" onChange={checked => patch({ borderless: checked })} />
                                        <Toggle checked={!!config.record} label="录像" onChange={checked => patch({ record: checked })} />
                                    </div>
                                </div>
                            </>
                        )}

                        {isCamera && <div className="win-info-box">摄像头模式的镜头、比例、手电筒、缩放等参数在“高级设置”里调整。</div>}

                        <div className="win-action-row">
                            <span className="win-note">{isHarmony ? 'HarmonyOS PC Mode · CastPlusDisplay · 低延迟' : isDesktop ? 'Android 虚拟显示' : isCamera ? '摄像头采集' : '手机屏幕镜像'}</span>
                            <button className={`win-button primary large ${isRunning ? 'danger' : ''}`} disabled={!selectedDevice} onClick={isRunning ? onStop : onStart}>
                                {isRunning ? '停止' : isHarmony ? '启动鸿蒙电脑模式' : '开始'}
                            </button>
                        </div>
                    </section>

                    <details className="win-details">
                        <summary>高级设置</summary>
                        <div className="win-details-body native-advanced">
                            <ControlPanel
                                config={config}
                                setConfig={setConfig}
                                onStart={onStart}
                                onStop={onStop}
                                isRunning={isRunning}
                                detectedCameras={detectedCameras}
                                renderDriverSupport={renderDriverSupport}
                                onListOptions={onListOptions}
                            />
                        </div>
                    </details>

                    <details className="win-details">
                        <summary>快捷键</summary>
                        <div className="win-details-body"><ShortcutsPanel /></div>
                    </details>

                    <details className="win-details win-log-details">
                        <summary>日志 <span>{logs.length ? `${logs.length} 条` : ''}</span></summary>
                        <div className="win-details-body">
                            <LogPanel logs={logs} onClear={onClearLogs} onAddLog={onAddLog} onRunCommand={onRunCommand} />
                        </div>
                    </details>
                </main>
            </div>
        </div>
    );
}
'''

LIGHT_CSS = r'''.win-native {
    --win-bg: #f3f3f3;
    --win-surface: #ffffff;
    --win-surface-2: #f8f8f8;
    --win-border: #d1d1d1;
    --win-border-strong: #b8b8b8;
    --win-text: #1a1a1a;
    --win-muted: #616161;
    --win-accent: #0067c0;
    --win-accent-hover: #005a9e;
    --win-danger: #c42b1c;
    min-height: 100vh;
    background: var(--win-bg);
    color: var(--win-text);
    font-family: "Segoe UI Variable", "Segoe UI", system-ui, sans-serif;
    font-size: 13px;
}

[data-mode='dark'] .win-native,
[data-mode='system'] .win-native {
    --win-bg: #202020;
    --win-surface: #2b2b2b;
    --win-surface-2: #252525;
    --win-border: #414141;
    --win-border-strong: #555555;
    --win-text: #f2f2f2;
    --win-muted: #b8b8b8;
    --win-accent: #60cdff;
    --win-accent-hover: #76d6ff;
    --win-danger: #ff99a4;
}

.win-titlebar {
    height: 54px;
    padding: 0 18px;
    display: grid;
    grid-template-columns: minmax(180px, 1fr) auto minmax(280px, 1fr);
    align-items: center;
    gap: 16px;
    background: var(--win-surface);
    border-bottom: 1px solid var(--win-border);
}

.win-brand, .win-device-status, .win-title-actions, .win-inline-input, .win-action-row { display: flex; align-items: center; }
.win-brand { gap: 10px; }
.win-brand > div:last-child { display: flex; align-items: baseline; gap: 8px; }
.win-brand strong { font-size: 14px; font-weight: 600; }
.win-brand span, .win-connection-state, .win-download-progress { color: var(--win-muted); font-size: 12px; }
.win-app-icon { width: 28px; height: 28px; border-radius: 6px; display: grid; place-items: center; background: var(--win-accent); color: #fff; font-weight: 700; }
.win-device-status { gap: 8px; min-width: 0; }
.win-device-name { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.win-status-dot { width: 8px; height: 8px; border-radius: 50%; background: #8a8a8a; }
.win-status-dot.online { background: #0f9d58; }
.win-title-actions { justify-content: flex-end; gap: 8px; }

.win-body { display: grid; grid-template-columns: 248px minmax(0, 1fr); min-height: calc(100vh - 54px); }
.win-sidebar { background: var(--win-surface-2); border-right: 1px solid var(--win-border); padding: 14px 12px 20px; overflow-y: auto; }
.win-content { padding: 22px 26px 34px; max-width: 980px; width: 100%; margin: 0 auto; }
.win-section-title { padding: 0 8px 8px; color: var(--win-muted); font-size: 12px; font-weight: 600; }

.win-panel, .win-details { background: var(--win-surface); border: 1px solid var(--win-border); border-radius: 8px; }
.win-primary-panel { padding: 22px; }
.win-section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 22px; }
.win-section-heading h1 { margin: 0 0 4px; font-size: 20px; font-weight: 600; line-height: 1.2; }
.win-section-heading p { margin: 0; color: var(--win-muted); font-size: 12px; }
.win-binary-state { color: var(--win-muted); font-size: 12px; white-space: nowrap; }
.win-field-group { margin-bottom: 20px; }
.win-label, .win-field > span { display: block; color: var(--win-muted); font-size: 12px; margin-bottom: 6px; }
.win-settings-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
.win-field { min-width: 0; }
.win-inline-input { gap: 7px; }
.win-inline-input .win-input { flex: 1; min-width: 0; }
.win-inline-input > span { color: var(--win-muted); }

.win-segmented { display: grid; border: 1px solid var(--win-border); border-radius: 6px; overflow: hidden; background: var(--win-surface-2); }
.win-segmented.four { grid-template-columns: repeat(4, 1fr); }
.win-segmented button { min-height: 34px; padding: 5px 10px; border: 0; border-right: 1px solid var(--win-border); background: transparent; color: var(--win-text); font: inherit; cursor: pointer; }
.win-segmented button:last-child { border-right: 0; }
.win-segmented button:hover { background: color-mix(in srgb, var(--win-accent) 8%, transparent); }
.win-segmented button.active { background: color-mix(in srgb, var(--win-accent) 15%, var(--win-surface)); color: var(--win-accent); box-shadow: inset 0 -2px 0 var(--win-accent); font-weight: 600; }

.win-input, .win-select { height: 32px; width: 100%; box-sizing: border-box; border: 1px solid var(--win-border-strong); border-radius: 4px; background: var(--win-surface); color: var(--win-text); padding: 4px 9px; font: inherit; outline: none; }
.win-input:focus, .win-select:focus { border-color: var(--win-accent); box-shadow: inset 0 -1px 0 var(--win-accent); }
.win-select.compact { width: auto; min-width: 104px; }

.win-divider { height: 1px; background: var(--win-border); margin: 20px 0; }
.win-row-section { display: grid; grid-template-columns: 80px 1fr; gap: 10px 18px; align-items: start; }
.win-row-title { font-weight: 600; padding-top: 2px; }
.win-toggle-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 18px; }
.win-toggle-grid.behavior { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.win-toggle { display: inline-flex; align-items: center; gap: 8px; min-height: 28px; cursor: pointer; user-select: none; }
.win-toggle input { accent-color: var(--win-accent); width: 15px; height: 15px; }
.win-toggle.is-disabled { opacity: .62; cursor: default; }
.win-note { color: var(--win-muted); font-size: 12px; grid-column: 2 / -1; }
.win-info-box { padding: 12px; border: 1px solid var(--win-border); border-radius: 6px; background: var(--win-surface-2); color: var(--win-muted); }

.win-action-row { justify-content: space-between; gap: 16px; margin-top: 24px; padding-top: 18px; border-top: 1px solid var(--win-border); }
.win-button { min-height: 30px; border: 1px solid var(--win-border-strong); border-radius: 4px; padding: 4px 12px; background: var(--win-surface); color: var(--win-text); font: inherit; cursor: pointer; }
.win-button:hover { background: var(--win-surface-2); }
.win-button.ghost { border-color: transparent; background: transparent; color: var(--win-muted); }
.win-button.primary { border-color: var(--win-accent); background: var(--win-accent); color: #fff; font-weight: 600; }
[data-mode='dark'] .win-button.primary { color: #00364d; }
.win-button.primary:hover { background: var(--win-accent-hover); }
.win-button.primary.danger { background: var(--win-danger); border-color: var(--win-danger); color: #fff; }
.win-button.large { min-height: 36px; padding-inline: 20px; }
.win-button:disabled { opacity: .45; cursor: default; }

.win-details { margin-top: 12px; overflow: hidden; }
.win-details > summary { cursor: pointer; list-style: none; padding: 12px 14px; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }
.win-details > summary::-webkit-details-marker { display: none; }
.win-details > summary::before { content: '›'; color: var(--win-muted); display: inline-block; margin-right: 8px; transition: transform .12s ease; }
.win-details[open] > summary::before { transform: rotate(90deg); }
.win-details-body { border-top: 1px solid var(--win-border); padding: 14px; }

/* Flatten the inherited ScrcpyGUI components when they are used inside the new shell. */
.win-native .glass { background: transparent !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important; box-shadow: none !important; }
.win-native [class*="shadow-"] { box-shadow: none !important; }
.win-native [class*="backdrop-blur"] { backdrop-filter: none !important; -webkit-backdrop-filter: none !important; }
.win-native .win-sidebar .glass, .win-native .native-advanced .glass { border-color: var(--win-border) !important; background: var(--win-surface) !important; }
.win-native .win-sidebar [class*="rounded-2xl"], .win-native .win-sidebar [class*="rounded-xl"], .win-native .native-advanced [class*="rounded-2xl"], .win-native .native-advanced [class*="rounded-xl"] { border-radius: 6px !important; }
.win-native .native-advanced main { display: block; }
.win-native .native-advanced main > * { margin-bottom: 10px; }
.win-native .native-advanced button, .win-native .win-sidebar button { transition-duration: 0ms !important; }

@media (max-width: 980px) {
    .win-titlebar { grid-template-columns: 1fr auto; }
    .win-device-status { display: none; }
    .win-body { grid-template-columns: 210px minmax(0, 1fr); }
    .win-settings-grid, .win-toggle-grid.behavior { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .win-segmented.four { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 720px) {
    .win-titlebar { height: auto; min-height: 54px; grid-template-columns: 1fr; padding-block: 10px; }
    .win-title-actions { justify-content: flex-start; flex-wrap: wrap; }
    .win-body { display: block; }
    .win-sidebar { border-right: 0; border-bottom: 1px solid var(--win-border); max-height: 260px; }
    .win-content { box-sizing: border-box; padding: 14px; }
    .win-settings-grid, .win-toggle-grid.behavior, .win-toggle-grid { grid-template-columns: 1fr; }
    .win-row-section { grid-template-columns: 1fr; }
    .win-note { grid-column: 1; }
}
'''

write_text("src/components/LightWorkspace.tsx", LIGHT_WORKSPACE)
write_text("src/light-ui.css", LIGHT_CSS)

app_path = "src/App.tsx"
app = read_text(app_path)
for line in [
    'import Sidebar from "./components/Sidebar";\n',
    'import ControlPanel from "./components/ControlPanel";\n',
    'import LogPanel from "./components/LogPanel";\n',
    'import Header from "./components/Header";\n',
    'import SessionBehavior from "./components/SessionBehavior";\n',
    'import ShortcutsPanel from "./components/ShortcutsPanel";\n',
    'import Footer from "./components/Footer";\n',
]:
    app = app.replace(line, "")

needle = 'import ErrorBoundary from "./components/ErrorBoundary";\n'
if needle not in app:
    raise RuntimeError("Could not find ErrorBoundary import in App.tsx")
app = app.replace(needle, 'import LightWorkspace from "./components/LightWorkspace";\nimport "./light-ui.css";\n' + needle, 1)

start = app.find('  return (\n    <ErrorBoundary>')
end_marker = '  );\n}\n\nexport default App;'
end = app.rfind(end_marker)
if start < 0 or end < 0:
    raise RuntimeError("Could not locate App.tsx return block")

new_return = r'''  return (
    <ErrorBoundary>
      <LightWorkspace
        config={config}
        setConfig={setConfig}
        onStart={handleStart}
        onStop={handleStop}
        isRunning={sessionRunning}
        devices={devices}
        deviceModels={deviceModels}
        deviceFriendlyNames={deviceFriendlyNames}
        runningDevices={runningDevices}
        onRefresh={handleRefresh}
        onKillAdb={handleKillAdb}
        selectedDevice={activeDevice}
        onSelectDevice={setActiveDevice}
        onPair={pairDevice}
        onConnect={connectDevice}
        isRefreshing={isRefreshing}
        onFilePush={handleFileBrowse}
        historyDevices={historyDevices}
        clearHistory={clearHistory}
        mdnsDevices={mdnsDevices}
        logs={logs}
        onClearLogs={clearLogs}
        onAddLog={(msg) => setLogs((prev: string[]) => [...prev.slice(-100), msg])}
        onRunCommand={runTerminalCommand}
        detectedCameras={detectedCameras}
        renderDriverSupport={renderDriverSupport}
        onListOptions={(arg) => { if (activeDevice) listScrcpyOptions(activeDevice, arg); }}
        binaryStatus={scrcpyStatus}
        onDownload={downloadScrcpy}
        onSetPath={handleSetPath}
        onResetPath={handleResetPath}
        isDownloading={isDownloading}
        downloadProgress={downloadProgress}
        version={appVersion}
        colorMode={colorMode}
        onColorModeChange={setColorMode}
      />

      <OnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
        binaryStatus={scrcpyStatus}
        onDownload={downloadScrcpy}
        isDownloading={isDownloading}
        downloadProgress={downloadProgress}
        onComplete={completeOnboarding}
      />

      <ThemedModal
        isOpen={alertState.isOpen}
        onClose={() => setAlertState(prev => ({ ...prev, isOpen: false }))}
        title={alertState.title}
        message={alertState.message}
        kind={alertState.kind}
        actionLabel={alertState.actionLabel}
        onAction={alertState.onAction}
        showCancel={alertState.showCancel}
        cancelLabel={alertState.cancelLabel}
        onCancel={alertState.onCancel}
      />
    </ErrorBoundary>
  );
}

export default App;'''

app = app[:start] + new_return
write_text(app_path, app)

print("Windows-native lightweight UI applied successfully.")
