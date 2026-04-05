# XRay_MSU

Расчёт порошковой рентгеновской дифракции для заданной кристаллической структуры: отражения, структурный фактор, кратность, L/P-факторы, нормировка, свёртка пиков (Кальотти + профиль). Есть **консольный сценарий** с конфигом OmegaConf и **GUI** на Tk/matplotlib.

**Подробное описание алгоритма:** [doc/README.md](doc/README.md).

## Требования

- **Python ≥ 3.12**
- Рекомендуется **[uv](https://docs.astral.sh/uv/)** (`uv sync`). В `pyproject.toml` задано `python-preference = "system"`, чтобы по возможности использовать системный интерпретатор с рабочим **tkinter** (на Linux см. `packaging/check_linux_tkinter_ldd.py` и пакеты `python3-tk` / `python3.12-tk`).

## Установка

```bash
git clone <url> XRay_MSU && cd XRay_MSU
uv sync                    # или: make install
uv sync --group dev        # PyInstaller для сборки бинарников
```

## Запуск

| Задача | Команда |
|--------|---------|
| CLI (конфиг задаётся в `cmd/main.py`, по умолчанию YAML из `config/`) | `uv run python cmd/main.py` или `make run` |
| GUI | `uv run python -m src` или `make gui` |

Результаты CLI пишутся в **`runs/<имя_образца>/`**: `*.tsv`, `G.csv`, `Gstar.csv`, графики `*_powder.png` и структура `*.png`. После расчёта из GUI набор файлов тот же.

Конфигурации-примеры лежат в **`config/`** (YAML), данные АФФ — **`data/f0_WaasKirf.dat`**.

## Сборка бинарников (PyInstaller)

- **Linux:** `make dist-gui` / `make dist-cli` или `./packaging/build-ubuntu.sh` — GUI в виде каталога `dist/xray-msu-gui/`, CLI — один файл `dist/xray-msu-cli`.
- **Windows:** `make dist-win` или `packaging/build-windows.ps1` / `build-windows.bat` → `dist/*.exe`.

Подробности в комментариях к `packaging/*.spec` и в `make help`.

## GitHub Actions и релизы

- Workflow **[build-binaries](.github/workflows/build-binaries.yml)** на push в `main` (по путям исходников) собирает артефакты для **Windows** и **Linux**; вложения можно скачать на вкладке **Actions**.
- По push тега **`v*`** запускается **[release](.github/workflows/release.yml)**: в одном run собираются **windows** и **linux**, затем job **publish** скачивает артефакты и создаёт **GitHub Release** с `xray-msu-gui.exe`, `xray-msu-cli.exe`, `xray-msu-linux-amd64.tar.gz`.

Создание релиза:

```bash
git tag -a v0.1.0 -m "0.1.0"
git push origin v0.1.0
```

Для записи релизов у репозитория в **Settings → Actions → General** должны быть разрешены права workflow на запись в репозиторий (по умолчанию для `GITHUB_TOKEN`).

## Документация в PDF

Из корня (нужны pandoc, XeLaTeX, шрифты DejaVu):

```bash
make doc-pdf
```

## Структура (кратко)

| Путь | Назначение |
|------|------------|
| `src/` | Модели: кристалл, порошковый паттерн, симметрия |
| `src/__main__.py` | Точка входа GUI (`python -m src`) |
| `cmd/main.py` | CLI с OmegaConf |
| `config/` | YAML-конфиги образцов |
| `packaging/` | PyInstaller spec, скрипты сборки, проверка tkinter на Linux |
| `entry_gui.py`, `entry_cli.py` | Входы для frozen-сборок |

## Линтинг

```bash
make lint          # проверка
make format        # правки
```
