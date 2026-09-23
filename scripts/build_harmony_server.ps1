$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$work = Join-Path $env:TEMP "scrcpy-harmony-server-v4.1"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }

git clone --depth 1 --branch v4.1 https://github.com/Genymobile/scrcpy.git $work

$path = Join-Path $work "server/src/main/java/com/genymobile/scrcpy/video/NewDisplayCapture.java"
$content = Get-Content -Raw $path
$old = 'createNewVirtualDisplay("scrcpy", displaySize.getWidth(), displaySize.getHeight(), dpi, surface, flags)'
$new = 'createNewVirtualDisplay("CastPlusDisplay", displaySize.getWidth(), displaySize.getHeight(), dpi, surface, flags)'
$count = ([regex]::Matches($content, [regex]::Escape($old))).Count
if ($count -ne 1) { throw "Expected exactly one patch target, found $count" }
Set-Content -Path $path -Value ($content.Replace($old, $new)) -Encoding utf8 -NoNewline

Push-Location $work
.\gradlew.bat -p server assembleRelease --stacktrace
Pop-Location

$outDir = Join-Path $root "src-tauri/resources"
New-Item -ItemType Directory -Force $outDir | Out-Null
$out = Join-Path $outDir "scrcpy-server-harmony"
Copy-Item (Join-Path $work "server/build/outputs/apk/release/server-release-unsigned.apk") $out -Force
python -c "import zipfile; p=r'$out'; z=zipfile.ZipFile(p); d=z.read('classes.dex'); assert b'CastPlusDisplay' in d; print('Harmony server verified:', len(d), 'DEX bytes')"
Get-FileHash $out -Algorithm SHA256
