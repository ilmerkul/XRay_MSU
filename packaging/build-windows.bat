@echo off
REM Сборка xray-msu-gui.exe и xray-msu-cli.exe (PyInstaller). Запуск из репозитория:
REM   packaging\build-windows.bat
setlocal
cd /d "%~dp0.."
set "PYINSTALLER_SPEC_ROOT=%CD%"

where uv >nul 2>&1
if %ERRORLEVEL% equ 0 (
  call uv sync --group dev
  call uv run --group dev pyinstaller "%~dp0xray-msu-gui.spec" --noconfirm
  call uv run --group dev pyinstaller "%~dp0xray-msu-cli.spec" --noconfirm
  goto :done
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
  py -m pip install -q "pyinstaller>=6.6.0"
  py -m PyInstaller "%~dp0xray-msu-gui.spec" --noconfirm
  py -m PyInstaller "%~dp0xray-msu-cli.spec" --noconfirm
  goto :done
)

python -m pip install -q "pyinstaller>=6.6.0"
python -m PyInstaller "%~dp0xray-msu-gui.spec" --noconfirm
python -m PyInstaller "%~dp0xray-msu-cli.spec" --noconfirm

:done
echo.
echo Готово: %CD%\dist\xray-msu-gui.exe и xray-msu-cli.exe
endlocal
