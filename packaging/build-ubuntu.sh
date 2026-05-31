#!/usr/bin/env bash
# Сборка PyInstaller на Ubuntu/Debian.
# GUI: каталог dist/xray-msu-gui/ (запуск: dist/xray-msu-gui/xray-msu-gui). CLI: dist/xray-msu-cli.
# Системные библиотеки Tcl/Tk должны совпадать с тем, с чем слинкован _tkinter вашего Python.
#   sudo apt-get update && sudo apt-get install -y python3-tk
# Если libtcl9*.so => not found и в apt нет libtcl9*: см. packaging/check_linux_tkinter_ldd.py и pyproject [tool.uv].
# Кратко: sudo apt install python3-tk; rm -rf .venv; uv sync --extra dev  (нужен системный Python ≥ requires-python)
#
# Использование из корня репозитория:
#   chmod +x packaging/build-ubuntu.sh
#   ./packaging/build-ubuntu.sh          # gui + cli
#   ./packaging/build-ubuntu.sh gui
#   ./packaging/build-ubuntu.sh cli

set -euo pipefail

TARGET="${1:-all}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYINSTALLER_SPEC_ROOT="$REPO_ROOT"
export MPLBACKEND="${MPLBACKEND:-TkAgg}"
cd "$REPO_ROOT"

run_gui() {
  if command -v uv >/dev/null 2>&1; then
    uv run --extra dev python "$SCRIPT_DIR/check_linux_tkinter_ldd.py"
    uv run --extra dev pyinstaller "$SCRIPT_DIR/xray-msu-gui.spec" --noconfirm
  else
    python3 "$SCRIPT_DIR/check_linux_tkinter_ldd.py"
    python3 -m PyInstaller "$SCRIPT_DIR/xray-msu-gui.spec" --noconfirm
  fi
}

run_cli() {
  if command -v uv >/dev/null 2>&1; then
    uv run --extra dev pyinstaller "$SCRIPT_DIR/xray-msu-cli.spec" --noconfirm
  else
    python3 -m PyInstaller "$SCRIPT_DIR/xray-msu-cli.spec" --noconfirm
  fi
}

if command -v uv >/dev/null 2>&1; then
  uv sync --extra dev
else
  python3 -m pip install -q "pyinstaller>=6.6.0"
fi

case "$TARGET" in
  gui) run_gui ;;
  cli) run_cli ;;
  all)
    run_gui
    run_cli
    ;;
  *)
    echo "Usage: $0 [gui|cli|all]" >&2
    exit 1
    ;;
esac

echo ""
echo "Готово: $REPO_ROOT/dist/xray-msu-gui/xray-msu-gui (GUI), dist/xray-msu-cli (CLI)"
