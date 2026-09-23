import { useEffect, useState } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { open } from "@tauri-apps/plugin-dialog";
import LightWorkspace from "./components/LightWorkspace";
import "./light-ui.css";
import ErrorBoundary from "./components/ErrorBoundary";
import OnboardingModal from "./components/OnboardingModal";
import ThemedModal from "./components/ThemedModal";
import { useScrcpy } from "./hooks/useScrcpy";
import { getVersion } from '@tauri-apps/api/app';
import { useI18n } from "./i18n";

function App() {
  const { t } = useI18n();
  const {
    devices,
    deviceModels,
    deviceFriendlyNames,
    logs,
    activeDevice,
    setActiveDevice,
    refreshDevices,
    refreshDevicesUntilSettled,
    runScrcpy,
    stopScrcpy,
    downloadScrcpy,
    checkScrcpy,
    scrcpyStatus,
    setLogs,
    isDownloading,
    downloadProgress,
    pairDevice,
    connectDevice,
    listScrcpyOptions,
    runTerminalCommand,
    runningDevices,
    isRefreshing,
    sessionRunning,
    clearLogs,
    detectedCameras,
    renderDriverSupport,
    mdnsDevices,
    config,
    setConfig,
    colorMode,
    setColorMode,
    pushFile,
    installApk,
    historyDevices,
    clearHistory,
    isOnboardingOpen,
    setIsOnboardingOpen,
    completeOnboarding
  } = useScrcpy();

  const [alertState, setAlertState] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    kind: 'warning' | 'error' | 'info' | 'success';
    actionLabel?: string;
    onAction?: () => void;
    showCancel?: boolean;
    cancelLabel?: string;
    onCancel?: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    kind: 'info'
  });

  const [appVersion, setAppVersion] = useState("3.3.0");
  const [lastCheckedPath, setLastCheckedPath] = useState<string | undefined>(undefined);
  const [hasCheckedUpdate, setHasCheckedUpdate] = useState(false);

  const showAlert = (
    title: string,
    message: string,
    kind: 'warning' | 'error' | 'info' | 'success' = 'info',
    actionLabel = 'OK',
    onAction?: () => void,
    showCancel = false,
    cancelLabel = 'Cancel',
    onCancel?: () => void
  ) => {
    setAlertState({
      isOpen: true,
      title,
      message,
      kind,
      actionLabel,
      onAction,
      showCancel,
      cancelLabel,
      onCancel
    });
  };

  useEffect(() => {
    // Initial setup: fetch version and close splashscreen
    const initApp = async () => {
      try {
        const v = await getVersion();
        setAppVersion(v);

        const { invoke } = await import('@tauri-apps/api/core');
        await invoke('close_splashscreen');
      } catch (e) {
        console.error("Initialization failed:", e);
      }
    };

    const timer = setTimeout(initApp, 500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    // Initial check (once on mount) - Silent to avoid log clatter. adb's own
    // reconnect of an already-paired device can lag a beat behind the app
    // opening, so keep checking briefly instead of a single refresh that
    // might land before adb has caught up.
    checkScrcpy(config.scrcpyPath);
    refreshDevicesUntilSettled(config.scrcpyPath);
  }, []);

  useEffect(() => {
    if (scrcpyStatus.found && (!hasCheckedUpdate || config.scrcpyPath !== lastCheckedPath) && !isDownloading) {
      setHasCheckedUpdate(true);
      setLastCheckedPath(config.scrcpyPath);
      
      const runCheck = async () => {
        try {
          const { invoke } = await import('@tauri-apps/api/core');
          const updateRes: any = await invoke('check_scrcpy_update', { customPath: config.scrcpyPath });
          if (updateRes && updateRes.update_available) {
            showAlert(
              t('alerts.updateAvailableTitle'),
              t('alerts.updateAvailableMessage', {
                local: updateRes.local_version || 'unknown',
                latest: updateRes.latest_version || 'unknown'
              }),
              'info',
              t('alerts.updateBtn'),
              async () => {
                if (config.scrcpyPath) {
                  setConfig(prev => ({ ...prev, scrcpyPath: undefined }));
                }
                await downloadScrcpy();
              },
              true,
              t('alerts.cancelBtn')
            );
          }
        } catch (e) {
          console.error("Failed to check for scrcpy updates:", e);
        }
      };
      runCheck();
    } else if (!scrcpyStatus.found) {
      setHasCheckedUpdate(false);
    }
  }, [scrcpyStatus.found, config.scrcpyPath, isDownloading, hasCheckedUpdate, lastCheckedPath, t]);

  useEffect(() => {
    // Global Drag and Drop Listener (re-bind only if activeDevice changes)
    const unlisten = getCurrentWindow().listen<{ paths: string[] }>("tauri://drag-drop", (event) => {
      if (!activeDevice) {
        setLogs(prev => [...prev.slice(-100), t('logs.noDeviceForDragDrop')]);
        return;
      }

      const paths = event.payload.paths;
      if (paths && paths.length > 0) {
        paths.forEach(path => handleFileOperation(path));
      }
    });

    return () => {
      unlisten.then(f => f());
    };
  }, [activeDevice]);

  useEffect(() => {
    // Keep the Rust side's notion of "the selected device" in sync, so the
    // Ctrl+Alt+Shift+C global shortcut (a real OS-level hotkey registered in
    // shortcuts.rs, not a webview keydown listener) knows which mirror window
    // to recentre even when no app window has keyboard focus.
    const device = activeDevice && runningDevices.includes(activeDevice) ? activeDevice : null;
    (async () => {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('set_active_device', { device });
    })();
  }, [activeDevice, runningDevices]);

  useEffect(() => {
    if (activeDevice) {
      setConfig(prev => ({ ...prev, device: activeDevice }));
    }
  }, [activeDevice]);

  const handleStart = async () => {
    if (!activeDevice) {
      showAlert(t('alerts.noDeviceSelectedTitle'), t('alerts.noDeviceSelectedMessage'), "warning");
      return;
    }
    await runScrcpy(config);
  };

  const handleStop = async () => {
    if (!activeDevice) return;
    await stopScrcpy(activeDevice);
  };

  const handleRefresh = () => {
    refreshDevices();
  };

  const handleKillAdb = async () => {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('kill_adb', { customPath: config.scrcpyPath });
      refreshDevices(config.scrcpyPath);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileOperation = async (path: string) => {
    if (!activeDevice) return;

    const isApk = path.toLowerCase().endsWith('.apk');
    if (isApk) {
      await installApk(activeDevice, path);
    } else {
      await pushFile(activeDevice, path);
    }
  };

  const handleFileBrowse = async () => {
    if (!activeDevice) return;
    try {
      const selected = await open({
        multiple: true,
        filters: [
          {
            name: 'All Files',
            extensions: ['*']
          },
          {
            name: 'Android App (APK)',
            extensions: ['apk']
          }
        ]
      });

      if (selected) {
        if (Array.isArray(selected)) {
          selected.forEach(path => handleFileOperation(path));
        } else {
          handleFileOperation(selected);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSetPath = async () => {
    try {
      let startPath = config.scrcpyPath;
      if (!startPath) {
        const { invoke } = await import('@tauri-apps/api/core');
        startPath = await invoke<string>('get_scrcpy_bin_dir').catch(() => '');
      }
      const selected = await open({
        directory: true,
        multiple: false,
        defaultPath: startPath || undefined
      });
      if (selected && typeof selected === 'string') {
        setConfig(prev => ({ ...prev, scrcpyPath: selected }));
        setLogs(prev => [...prev.slice(-100), t('logs.customScrcpyPathSet', { path: selected })]);
        // Trigger a check with the new path
        setTimeout(() => checkScrcpy(selected), 100);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleResetPath = async () => {
    setConfig(prev => ({ ...prev, scrcpyPath: undefined }));
    setLogs(prev => [...prev.slice(-100), t('logs.customScrcpyPathCleared')]);
    // Trigger a check with no custom path
    setTimeout(() => checkScrcpy(undefined), 100);
  };

  return (
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

export default App;