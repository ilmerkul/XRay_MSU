# XRay_MSU — запуск из корня репозитория (пути config/, data/, runs/).
ROOT := $(abspath .)
PYTHON ?= python3
# Пустая строка, если uv нет в PATH
HAS_UV := $(shell command -v uv >/dev/null 2>&1 && echo yes)
# Windows: cmd задаёт OS=Windows_NT; Git Bash / MSYS: uname с MINGW/MSYS/CYGWIN
UNAME_S := $(shell uname -s 2>/dev/null)
IS_WIN :=
ifneq ($(filter Windows_NT,$(OS)),)
IS_WIN := yes
endif
ifeq ($(IS_WIN),)
ifneq ($(findstring MINGW,$(UNAME_S)),)
IS_WIN := yes
endif
endif
ifeq ($(IS_WIN),)
ifneq ($(findstring MSYS,$(UNAME_S)),)
IS_WIN := yes
endif
endif
ifeq ($(IS_WIN),)
ifneq ($(findstring CYGWIN,$(UNAME_S)),)
IS_WIN := yes
endif
endif

# Документация → PDF (pandoc + xelatex): переопределите DOC_SRC / DOC_OUT / DOC_TITLE при необходимости
DOC_SRC ?= doc/README.md
DOC_OUT ?= doc/README.pdf
DOC_TITLE ?= XRay_MSU — алгоритм

.PHONY: help install sync run gui lint format check test clean doc-pdf doc-pdf-overview doc-pdf-all dist dist-gui dist-cli dist-win dist-win-gui dist-win-cli clean-dist

help: ## Показать цели
	@echo "XRay_MSU — make-цели (рабочий каталог: $(ROOT))"
	@echo ""
	@echo "  make install   — зависимости: uv sync или pip install -e ."
	@echo "  make sync      — то же, что install"
	@echo "  make run       — расчёт и график: entry_cli.py (конфиг внутри скрипта)"
	@echo "  make gui       — GUI: python -m src"
	@echo "  make lint      — ruff check"
	@echo "  make format    — ruff format"
	@echo "  make check     — lint + pytest"
	@echo "  make test      — pytest (tests/unit/)"
	@echo "  make clean     — удалить __pycache__ и кэш ruff"
	@echo "  make doc-pdf           — DOC_SRC → DOC_OUT (по умолчанию doc/README.md → doc/README.pdf)"
	@echo "  make doc-pdf-overview  — doc/README-overview.md → doc/README-overview.pdf"
	@echo "  make doc-pdf-all       — оба PDF (нужны pandoc, xelatex, шрифты DejaVu)"
	@echo "  make dist      — PyInstaller: GUI + CLI (на Windows — оба .exe через dist-gui/dist-cli)"
	@echo "  make dist-gui  — GUI: Windows → xray-msu-gui.exe; Linux — onedir + check_linux_tkinter_ldd"
	@echo "  make dist-cli  — CLI: Windows → xray-msu-cli.exe; иначе бинарник без .exe"
	@echo "  make dist-win / dist-win-gui / dist-win-cli — только Windows: .exe через PowerShell"
	@echo "  make clean-dist — удалить build/ и dist/"
	@echo "  Релиз на GitHub: git tag -a v0.1.0 -m msg && git push origin v0.1.0 → workflow release.yml прикрепит exe + linux .tar.gz"
	@echo "  Ubuntu/Linux:   ./packaging/build-ubuntu.sh или make dist / dist-gui / dist-cli"
	@echo ""
	@echo "Переменные: PYTHON=$(PYTHON)  (если без uv, активируйте venv с зависимостями)"

install sync: ## Установить зависимости проекта
ifeq ($(HAS_UV),yes)
	cd "$(ROOT)" && uv sync
else
	cd "$(ROOT)" && $(PYTHON) -m pip install \
		"numpy>=2.4.2" "matplotlib>=3.10.8" "scipy>=1.17.1" "omegaconf>=2.3.0" \
		"spglib>=2.7.0" "xraylib>=4.2.1" "ruff>=0.15.9" "customtkinter>=5.2.2" "pre-commit>=4.5.1"
endif

run: ## Пайплайн порошковой дифракции (OmegaConf + Plot)
ifeq ($(HAS_UV),yes)
	cd "$(ROOT)" && uv run python entry_cli.py
else
	cd "$(ROOT)" && $(PYTHON) entry_cli.py
endif

gui: ## Окно Tk / matplotlib (пакет src)
ifeq ($(HAS_UV),yes)
	cd "$(ROOT)" && uv run python -m src
else
	cd "$(ROOT)" && $(PYTHON) -m src
endif

lint: ## Проверка стиля (ruff)
ifeq ($(HAS_UV),yes)
	cd "$(ROOT)" && uv run ruff check src entry_cli.py entry_gui.py tests/unit
else
	cd "$(ROOT)" && $(PYTHON) -m ruff check src entry_cli.py entry_gui.py tests/unit
endif

check: lint test ## lint + pytest

test: ## Юнит- и интеграционные тесты (pytest)
ifeq ($(HAS_UV),yes)
	cd "$(ROOT)" && uv sync --group dev
	cd "$(ROOT)" && uv run --group dev pytest tests/unit -q
else
	cd "$(ROOT)" && $(PYTHON) -m pytest tests/unit -q
endif

format: ## Форматирование (ruff format)
ifeq ($(HAS_UV),yes)
	cd "$(ROOT)" && uv run ruff format src entry_cli.py entry_gui.py tests/unit
else
	cd "$(ROOT)" && $(PYTHON) -m ruff format src entry_cli.py entry_gui.py tests/unit
endif

clean: ## Кэши Python и ruff
	cd "$(ROOT)" && find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	cd "$(ROOT)" && rm -rf .ruff_cache .pytest_cache

doc-pdf: ## $(DOC_SRC) → $(DOC_OUT) (pandoc, xelatex, шрифты DejaVu)
	cd "$(ROOT)" && $(PYTHON) scripts/readme_md_for_pandoc.py "$(DOC_SRC)" > doc/.README_for_pdf.md
	cd "$(ROOT)" && pandoc doc/.README_for_pdf.md -o "$(DOC_OUT)" \
		--pdf-engine=xelatex \
		-V mainfont="DejaVu Serif" \
		-V sansfont="DejaVu Sans" \
		-V monofont="DejaVu Sans Mono" \
		-V geometry:margin=2.5cm \
		--metadata title="$(DOC_TITLE)" \
		-N
	rm -f "$(ROOT)/doc/.README_for_pdf.md"

doc-pdf-overview: ## doc/README-overview.md → doc/README-overview.pdf
	@$(MAKE) -C "$(ROOT)" doc-pdf \
		DOC_SRC=doc/README-overview.md \
		DOC_OUT=doc/README-overview.pdf \
		DOC_TITLE='XRay_MSU — обзор'

doc-pdf-all: doc-pdf doc-pdf-overview ## Собрать doc/README.pdf и doc/README-overview.pdf
	@true

dist: dist-gui dist-cli ## Собрать оба бинарника (PyInstaller)

dist-gui: ## GUI: Windows → xray-msu-gui.exe; Linux → onedir dist/xray-msu-gui/
ifeq ($(IS_WIN),yes)
	cd "$(ROOT)" && powershell.exe -NoProfile -ExecutionPolicy Bypass -File "packaging/build-windows.ps1" -Target gui
else
ifeq ($(HAS_UV),yes)
	cd "$(ROOT)" && uv sync --group dev
ifeq ($(shell uname -s),Linux)
	cd "$(ROOT)" && uv run --group dev python packaging/check_linux_tkinter_ldd.py
endif
	cd "$(ROOT)" && PYINSTALLER_SPEC_ROOT="$(ROOT)" uv run --group dev pyinstaller packaging/xray-msu-gui.spec --noconfirm
else
	cd "$(ROOT)" && $(PYTHON) -m pip install -q "pyinstaller>=6.6.0"
ifeq ($(shell uname -s),Linux)
	cd "$(ROOT)" && $(PYTHON) packaging/check_linux_tkinter_ldd.py
endif
	cd "$(ROOT)" && PYINSTALLER_SPEC_ROOT="$(ROOT)" $(PYTHON) -m PyInstaller packaging/xray-msu-gui.spec --noconfirm
endif
endif

dist-cli: ## CLI: Windows → xray-msu-cli.exe; иначе dist/xray-msu-cli
ifeq ($(IS_WIN),yes)
	cd "$(ROOT)" && powershell.exe -NoProfile -ExecutionPolicy Bypass -File "packaging/build-windows.ps1" -Target cli
else
ifeq ($(HAS_UV),yes)
	cd "$(ROOT)" && uv sync --group dev
	cd "$(ROOT)" && PYINSTALLER_SPEC_ROOT="$(ROOT)" uv run --group dev pyinstaller packaging/xray-msu-cli.spec --noconfirm
else
	cd "$(ROOT)" && $(PYTHON) -m pip install -q "pyinstaller>=6.6.0"
	cd "$(ROOT)" && PYINSTALLER_SPEC_ROOT="$(ROOT)" $(PYTHON) -m PyInstaller packaging/xray-msu-cli.spec --noconfirm
endif
endif

dist-win: ## Только Windows: оба .exe (как packaging/build-windows.ps1)
ifeq ($(IS_WIN),yes)
	cd "$(ROOT)" && powershell.exe -NoProfile -ExecutionPolicy Bypass -File "packaging/build-windows.ps1" -Target all
else
	@echo "make dist-win: запускайте на Windows (cmd с make + PowerShell или Git Bash)." >&2
	@exit 1
endif

dist-win-gui: ## Только Windows: dist/xray-msu-gui.exe
ifeq ($(IS_WIN),yes)
	cd "$(ROOT)" && powershell.exe -NoProfile -ExecutionPolicy Bypass -File "packaging/build-windows.ps1" -Target gui
else
	@echo "make dist-win-gui: только на Windows." >&2
	@exit 1
endif

dist-win-cli: ## Только Windows: dist/xray-msu-cli.exe
ifeq ($(IS_WIN),yes)
	cd "$(ROOT)" && powershell.exe -NoProfile -ExecutionPolicy Bypass -File "packaging/build-windows.ps1" -Target cli
else
	@echo "make dist-win-cli: только на Windows." >&2
	@exit 1
endif

clean-dist: ## Артефакты PyInstaller
	rm -rf "$(ROOT)/build" "$(ROOT)/dist"
