# Сборка однофайловых exe через PyInstaller (Windows).
# Требуется: Python 3.12+ (или py launcher), зависимости проекта; лучше без torch в окружении.
#
# Запуск (из репозитория, PowerShell):
#   .\packaging\build-windows.ps1
#   .\packaging\build-windows.ps1 -Target gui
#   .\packaging\build-windows.ps1 -Target cli

param(
    [ValidateSet("gui", "cli", "all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:PYINSTALLER_SPEC_ROOT = $RepoRoot
Set-Location $RepoRoot

function Invoke-Build {
    param([string]$SpecFile)
    $specPath = Join-Path $PSScriptRoot $SpecFile
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        & uv sync --group dev
        & uv run --group dev pyinstaller $specPath --noconfirm
    }
    elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -m pip install -q "pyinstaller>=6.6.0"
        & py -m PyInstaller $specPath --noconfirm
    }
    else {
        & python -m pip install -q "pyinstaller>=6.6.0"
        & python -m PyInstaller $specPath --noconfirm
    }
}

if ($Target -eq "gui" -or $Target -eq "all") {
    Invoke-Build "xray-msu-gui.spec"
}
if ($Target -eq "cli" -or $Target -eq "all") {
    Invoke-Build "xray-msu-cli.spec"
}

Write-Host ""
Write-Host "Артефакты: $RepoRoot\dist\xray-msu-gui.exe и dist\xray-msu-cli.exe"
