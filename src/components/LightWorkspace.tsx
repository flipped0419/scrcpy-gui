import type { Dispatch, SetStateAction } from 'react';
import type { MdnsDevice, RenderDriverSupport, ScrcpyConfig } from '../hooks/useScrcpy';
import Sidebar from './Sidebar';
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
        renderDriverSupport, binaryStatus, onDownload, onSetPath,
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
                                    <div className="win-input-controls">
                                        <div className="win-toggle-grid">
                                            <Toggle checked={isHarmony || !!config.hidMouse} disabled={isHarmony} label="UHID 鼠标" onChange={checked => patch({ hidMouse: checked })} />
                                            <Toggle checked={isHarmony || !!config.hidKeyboard} disabled={isHarmony} label="UHID 键盘" onChange={checked => patch({ hidKeyboard: checked })} />
                                        </div>
                                        {isHarmony && (
                                            <label className="win-field win-shortcut-field">
                                                <span>释放鼠标快捷键</span>
                                                <select
                                                    className="win-select"
                                                    value={config.shortcutMod || 'rctrl'}
                                                    onChange={e => patch({ shortcutMod: e.target.value as ScrcpyConfig['shortcutMod'] })}
                                                >
                                                    <option value="rctrl">右 Ctrl</option>
                                                    <option value="lctrl">左 Ctrl</option>
                                                    <option value="lalt">左 Alt</option>
                                                    <option value="ralt">右 Alt</option>
                                                    <option value="lsuper">左 Windows</option>
                                                    <option value="rsuper">右 Windows</option>
                                                </select>
                                            </label>
                                        )}
                                    </div>
                                    {isHarmony && <span className="win-note">该按键同时作为 scrcpy 快捷键修饰键；按下它可切换 UHID 鼠标捕获。默认右 Ctrl。</span>}
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
                        <div className="win-details-body win-advanced-only">
                            <section className="win-advanced-section">
                                <h3>视频与渲染</h3>
                                <div className="win-advanced-grid">
                                    <label className="win-field">
                                        <span>渲染器</span>
                                        <select className="win-select" value={config.renderDriver || 'auto'} onChange={e => patch({ renderDriver: e.target.value === 'auto' ? undefined : e.target.value })}>
                                            <option value="auto">自动</option>
                                            {renderDriverSupport.supportedDrivers.map(driver => (
                                                <option key={driver.id} value={driver.id}>{driver.label}</option>
                                            ))}
                                        </select>
                                    </label>
                                    <label className="win-field">
                                        <span>背景颜色</span>
                                        <input className="win-input" value={config.backgroundColor || ''} placeholder="#000000" onChange={e => patch({ backgroundColor: e.target.value })} />
                                    </label>
                                </div>
                                <div className="win-advanced-toggles">
                                    <Toggle checked={config.vsync !== false} label="VSync" onChange={checked => patch({ vsync: checked })} />
                                    <Toggle checked={!!config.ignoreVideoEncoderConstraints} label="忽略编码器尺寸限制" onChange={checked => patch({ ignoreVideoEncoderConstraints: checked })} />
                                    <Toggle checked={config.rememberWindowPosition !== false} label="记住窗口位置" onChange={checked => patch({ rememberWindowPosition: checked })} />
                                </div>
                            </section>

                            <section className="win-advanced-section">
                                <h3>音频与录像</h3>
                                <div className="win-advanced-grid">
                                    <label className="win-field">
                                        <span>音频编码</span>
                                        <select className="win-select" value={config.audioCodec || 'auto'} onChange={e => patch({ audioCodec: e.target.value })}>
                                            <option value="auto">自动</option>
                                            <option value="opus">Opus</option>
                                            <option value="aac">AAC</option>
                                            <option value="flac">FLAC</option>
                                            <option value="raw">RAW</option>
                                        </select>
                                    </label>
                                    <label className="win-field">
                                        <span>录像保存位置</span>
                                        <input className="win-input" value={config.recordPath || ''} onChange={e => patch({ recordPath: e.target.value })} />
                                    </label>
                                </div>
                            </section>

                            {mode === 'desktop' && (
                                <section className="win-advanced-section">
                                    <h3>虚拟桌面</h3>
                                    <div className="win-advanced-grid three">
                                        <label className="win-field">
                                            <span>显示方向</span>
                                            <select className="win-select" value={config.vdOrientation || 'auto'} onChange={e => patch({ vdOrientation: e.target.value as ScrcpyConfig['vdOrientation'] })}>
                                                <option value="auto">自动</option>
                                                <option value="landscape">横屏</option>
                                                <option value="portrait">竖屏</option>
                                            </select>
                                        </label>
                                        <label className="win-field"><span>自定义宽度</span><input className="win-input" type="number" min={320} value={config.vdWidth || 1920} onChange={e => patch({ vdWidth: Number(e.target.value) || 1920 })} /></label>
                                        <label className="win-field"><span>自定义高度</span><input className="win-input" type="number" min={320} value={config.vdHeight || 1080} onChange={e => patch({ vdHeight: Number(e.target.value) || 1080 })} /></label>
                                    </div>
                                    <div className="win-advanced-grid">
                                        <label className="win-field">
                                            <span>启动应用包名</span>
                                            <input className="win-input" value={config.startApp || ''} placeholder="com.example.app" onChange={e => patch({ startApp: e.target.value })} />
                                        </label>
                                    </div>
                                    <div className="win-advanced-toggles">
                                        <Toggle checked={!!config.flexDisplay} label="Flex Display" onChange={checked => patch({ flexDisplay: checked })} />
                                    </div>
                                </section>
                            )}

                            {mode === 'mirror' && (
                                <section className="win-advanced-section">
                                    <h3>手机屏幕输入</h3>
                                    <div className="win-advanced-toggles">
                                        <Toggle checked={!!config.otgPure} label="仅 OTG 控制" onChange={checked => patch({ otgPure: checked })} />
                                        <Toggle checked={config.aspectRatioLock !== false} label="锁定宽高比" onChange={checked => patch({ aspectRatioLock: checked })} />
                                    </div>
                                </section>
                            )}

                            {isCamera && (
                                <section className="win-advanced-section">
                                    <h3>摄像头</h3>
                                    <div className="win-advanced-grid three">
                                        <label className="win-field">
                                            <span>镜头方向</span>
                                            <select className="win-select" value={config.cameraFacing || 'front'} onChange={e => patch({ cameraFacing: e.target.value })}>
                                                <option value="front">前置</option>
                                                <option value="back">后置</option>
                                                <option value="external">外接</option>
                                            </select>
                                        </label>
                                        <label className="win-field">
                                            <span>摄像头 ID</span>
                                            <select className="win-select" value={config.cameraId || ''} onChange={e => patch({ cameraId: e.target.value })}>
                                                <option value="">自动</option>
                                                {detectedCameras.map(camera => <option key={camera.id} value={camera.id}>{camera.name || camera.id}</option>)}
                                            </select>
                                        </label>
                                        <label className="win-field"><span>宽高比</span><input className="win-input" value={config.cameraAr || ''} placeholder="sensor / 16:9" onChange={e => patch({ cameraAr: e.target.value })} /></label>
                                    </div>
                                    <div className="win-advanced-grid">
                                        <label className="win-field"><span>缩放</span><input className="win-input" type="number" min={1} step={0.1} value={config.cameraZoom || 1} onChange={e => patch({ cameraZoom: Number(e.target.value) || 1 })} /></label>
                                    </div>
                                    <div className="win-advanced-toggles">
                                        <Toggle checked={!!config.cameraHighSpeed} label="高速摄像" onChange={checked => patch({ cameraHighSpeed: checked })} />
                                        <Toggle checked={!!config.cameraTorch} label="手电筒" onChange={checked => patch({ cameraTorch: checked })} />
                                    </div>
                                </section>
                            )}

                            {isHarmony && (
                                <div className="win-info-box">鸿蒙电脑模式的分辨率、DPI、帧率、码率、编码、UHID 键鼠、释放鼠标快捷键和行为设置均在上方主面板配置，这里不再重复显示。</div>
                            )}
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
