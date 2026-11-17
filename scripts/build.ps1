param([switch]$PackageWithoutLaunch)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path (Get-Location) '.python\python.exe'
if (-not (Test-Path $python)) { $python = 'python' }
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
& $python -m PyInstaller --noconfirm --clean --windowed --onedir --name LogiZ407ControlPro --icon assets/app.ico --add-data 'assets;assets' --collect-submodules winrt --collect-submodules pycaw --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets run.py
if ($LASTEXITCODE -ne 0) { throw 'Executable build failed' }
& $python scripts/fix_runtime.py
& $python scripts/collect_licenses.py
if ($PackageWithoutLaunch) {
    Write-Warning 'Packaged execution verification skipped explicitly. Do not claim this executable was smoke-tested.'
} else {
    $process = Start-Process -FilePath 'dist\LogiZ407ControlPro\LogiZ407ControlPro.exe' -ArgumentList '--smoke-test' -WindowStyle Hidden -PassThru
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw 'Packaged application smoke test failed' }
}
$compiler = Join-Path (Get-Location) 'packaging\inno\ISCC.exe'
if (-not (Test-Path $compiler)) { $compiler = (Get-Command ISCC.exe -ErrorAction Stop).Source }
& $compiler packaging/installer.iss
if ($LASTEXITCODE -ne 0) { throw 'Installer build failed' }
Get-FileHash dist/installer/LogiZ407ControlPro-Setup.exe -Algorithm SHA256
