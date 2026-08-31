param(
    [string]$ScrcpyRef = "v4.1",
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $repoRoot "src-tauri/resources/scrcpy-server-harmony"
} elseif (-not [System.IO.Path]::IsPathRooted($OutputPath)) {
    $OutputPath = Join-Path $repoRoot $OutputPath
}

$workRoot = Join-Path $repoRoot ".build"
$scrcpyDir = Join-Path $workRoot "harmony-scrcpy"

Write-Host "[HarmonyOS] Repository root: $repoRoot"
Write-Host "[HarmonyOS] scrcpy ref: $ScrcpyRef"
Write-Host "[HarmonyOS] output: $OutputPath"

if (Test-Path $scrcpyDir) {
    Remove-Item -Recurse -Force $scrcpyDir
}
New-Item -ItemType Directory -Force $workRoot | Out-Null

Write-Host "[HarmonyOS] Cloning scrcpy..."
& git clone --depth 1 --branch $ScrcpyRef https://github.com/Genymobile/scrcpy.git $scrcpyDir
if ($LASTEXITCODE -ne 0) {
    throw "git clone failed with exit code $LASTEXITCODE"
}

$sourcePath = Join-Path $scrcpyDir "server/src/main/java/com/genymobile/scrcpy/video/NewDisplayCapture.java"
$content = [System.IO.File]::ReadAllText($sourcePath)
$old = 'createNewVirtualDisplay("scrcpy", displaySize.getWidth(), displaySize.getHeight(), dpi, surface, flags)'
$new = 'createNewVirtualDisplay("CastPlusDisplay", displaySize.getWidth(), displaySize.getHeight(), dpi, surface, flags)'

$matches = ([regex]::Matches($content, [regex]::Escape($old))).Count
if ($matches -ne 1) {
    throw "Expected exactly one virtual display patch target in NewDisplayCapture.java, found $matches"
}

$patched = $content.Replace($old, $new)
[System.IO.File]::WriteAllText($sourcePath, $patched, [System.Text.UTF8Encoding]::new($false))

Write-Host "[HarmonyOS] Patched virtual display name: scrcpy -> CastPlusDisplay"

Push-Location $scrcpyDir
try {
    if ($IsWindows) {
        & .\gradlew.bat -p server assembleRelease --stacktrace
    } else {
        & ./gradlew -p server assembleRelease --stacktrace
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Gradle build failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

$builtServer = Join-Path $scrcpyDir "server/build/outputs/apk/release/server-release-unsigned.apk"
if (-not (Test-Path $builtServer)) {
    throw "Built scrcpy server not found: $builtServer"
}

$outputDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force $outputDir | Out-Null
Copy-Item -Force $builtServer $OutputPath

# Verify that the patched display name is present in classes.dex.
$verifyScript = @'
import sys
import zipfile

path = sys.argv[1]
with zipfile.ZipFile(path) as archive:
    dex = archive.read("classes.dex")
assert b"CastPlusDisplay" in dex, "CastPlusDisplay not found in classes.dex"
print(f"[HarmonyOS] Verified CastPlusDisplay in classes.dex ({len(dex)} bytes)")
'@

$verifyScript | python - $OutputPath
if ($LASTEXITCODE -ne 0) {
    throw "Harmony server verification failed with exit code $LASTEXITCODE"
}

$hash = Get-FileHash $OutputPath -Algorithm SHA256
Write-Host "[HarmonyOS] Build complete"
Write-Host "[HarmonyOS] SHA256: $($hash.Hash)"
