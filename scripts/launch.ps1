$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
$pythonw = Join-Path $workspace '.python\pythonw.exe'
if (-not (Test-Path $pythonw)) {
    $pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source
}
Start-Process -FilePath $pythonw -ArgumentList ('"' + (Join-Path $workspace 'run.py') + '"') -WorkingDirectory $workspace -WindowStyle Hidden
