"""Фрагмент GUI: ConfigMixin."""

import fnmatch
import glob
import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import yaml

from ..runtime_layout import application_directory, ensure_runtime_layout, resource_path


class ConfigMixin:
    def find_config_dir(self):
        """Находит каталог с файлами конфигурации кристаллов.

        Returns:
            Путь к каталогу ``config`` (исходники, PyInstaller или frozen layout).
        """
        if getattr(sys, "frozen", False):
            return str(ensure_runtime_layout())
        rp = resource_path("config")
        if rp and os.path.isdir(rp):
            return rp
        if hasattr(sys, "_MEIPASS"):
            meipass_cfg = os.path.join(sys._MEIPASS, "config")
            if os.path.isdir(meipass_cfg):
                return meipass_cfg
        pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(pkg_root, "config")
        if os.path.isdir(candidate):
            return candidate
        parent_dir = os.path.dirname(pkg_root)
        candidate = os.path.join(parent_dir, "config")
        if os.path.isdir(candidate):
            return candidate
        return "config"

    def _config_repo_root(self) -> str:
        """Корень проекта для разрешения относительных путей конфигов.

        Returns:
            Каталог приложения (frozen) или родитель ``config_dir``.
        """
        if getattr(sys, "frozen", False):
            return str(application_directory())
        return os.path.dirname(self.config_dir) or "."

    def _user_config_dir(self) -> str:
        """Каталог пользовательских метаданных списка конфигов.

        Returns:
            Путь к ``config_dir``.
        """
        return self.config_dir

    def _config_list_meta_paths(self):
        """Пути к служебным файлам списка конфигураций.

        Returns:
            Кортеж ``(extra_paths.txt, ignore_list.txt, list_entries.txt)``.
        """
        d = self._user_config_dir()
        return (
            os.path.join(d, "extra_paths.txt"),
            os.path.join(d, "ignore_list.txt"),
            os.path.join(d, "list_entries.txt"),
        )

    @staticmethod
    def _normalize_config_path(raw: str, base: str) -> str:
        """Нормализует путь из файла списка относительно базового каталога.

        Args:
            raw: Строка пути из файла.
            base: Базовый каталог для относительных путей.

        Returns:
            Абсолютный нормализованный путь или пустая строка.
        """
        raw = raw.strip()
        if not raw:
            return ""
        if os.path.isabs(raw):
            return os.path.normpath(raw)
        return os.path.normpath(os.path.join(base, raw))

    def _path_for_list_entry_storage(self, path: str) -> str:
        """Формирует путь для записи в ``list_entries.txt`` (относительный, если можно).

        Args:
            path: Абсолютный путь к файлу или каталогу конфигурации.

        Returns:
            Относительный путь от ``_config_repo_root`` или исходный абсолютный.
        """
        path = os.path.normpath(os.path.abspath(path))
        base = self._config_repo_root()
        try:
            rel = os.path.relpath(path, base)
            if not rel.startswith(".."):
                return rel
        except ValueError:
            pass
        return path

    def _read_path_list_file(self, filepath: str) -> list[str]:
        """Читает список путей из текстового файла (по одному на строку).

        Args:
            filepath: Путь к файлу со списком.

        Returns:
            Список существующих нормализованных путей (комментарии пропускаются).
        """
        if not os.path.isfile(filepath):
            return []
        base = self._config_repo_root()
        out = []
        with open(filepath, encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                p = self._normalize_config_path(raw, base)
                if p and (os.path.isfile(p) or os.path.isdir(p)):
                    out.append(p)
        return out

    def _load_config_extra_dirs(self):
        """Загружает дополнительные каталоги поиска конфигов из ``extra_paths.txt``.

        Returns:
            Список путей к каталогам.
        """
        extra_paths_file, _, _ = self._config_list_meta_paths()
        return self._read_path_list_file(extra_paths_file)

    def _load_list_entries(self):
        """Собирает уникальные записи из ``list_entries.txt`` (user и bundled).

        Returns:
            Список путей к конфигам или каталогам без дубликатов.
        """
        seen = set()
        entries = []
        for path in (
            os.path.join(self._user_config_dir(), "list_entries.txt"),
            os.path.join(self.config_dir, "list_entries.txt"),
        ):
            for p in self._read_path_list_file(path):
                if p not in seen:
                    seen.add(p)
                    entries.append(p)
        return entries

    def _append_list_entry(self, path: str) -> None:
        """Добавляет путь в пользовательский ``list_entries.txt``.

        Args:
            path: Путь к файлу или каталогу конфигурации.

        Raises:
            FileNotFoundError: Если путь не существует.
        """
        path = os.path.normpath(os.path.abspath(path))
        if not os.path.isfile(path) and not os.path.isdir(path):
            raise FileNotFoundError(path)
        for existing in self._load_list_entries():
            if os.path.normpath(existing) == path:
                return
        user_dir = self._user_config_dir()
        os.makedirs(user_dir, exist_ok=True)
        list_file = os.path.join(user_dir, "list_entries.txt")
        store = self._path_for_list_entry_storage(path)
        need_newline = os.path.isfile(list_file) and os.path.getsize(list_file) > 0
        with open(list_file, "a", encoding="utf-8") as fh:
            if need_newline:
                fh.write("\n")
            fh.write(store + "\n")

    def _remove_list_entry_path(self, path: str) -> bool:
        """Удаляет путь из пользовательского ``list_entries.txt``.

        Args:
            path: Абсолютный путь, который нужно убрать из списка.

        Returns:
            ``True``, если запись была удалена.
        """
        path = os.path.normpath(os.path.abspath(path))
        list_file = os.path.join(self._user_config_dir(), "list_entries.txt")
        if not os.path.isfile(list_file):
            return False
        base = self._config_repo_root()
        kept = []
        removed = False
        with open(list_file, encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    kept.append(line if line.endswith("\n") else line + "\n")
                    continue
                p = self._normalize_config_path(raw, base)
                if p and os.path.normpath(p) == path:
                    removed = True
                    continue
                kept.append(line if line.endswith("\n") else line + "\n")
        if removed:
            with open(list_file, "w", encoding="utf-8") as fh:
                fh.writelines(kept)
        return removed

    def _load_config_ignore_patterns(self):
        """Загружает шаблоны скрытых конфигов из ``ignore_list.txt``.

        Returns:
            Список уникальных glob-шаблонов.
        """
        patterns = []
        seen = set()
        user = self._user_config_dir()
        for path in (
            os.path.join(self.config_dir, "ignore_list.txt"),
            os.path.join(user, "ignore_list.txt"),
        ):
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    raw = line.strip()
                    if raw and not raw.startswith("#") and raw not in seen:
                        seen.add(raw)
                        patterns.append(raw)
        return patterns

    def _append_ignore_pattern(self, pattern: str) -> None:
        """Добавляет шаблон в пользовательский ``ignore_list.txt``.

        Args:
            pattern: Имя файла или glob-шаблон для скрытия.
        """
        patterns = self._load_config_ignore_patterns()
        if pattern in patterns:
            return
        user_dir = self._user_config_dir()
        os.makedirs(user_dir, exist_ok=True)
        ignore_file = os.path.join(user_dir, "ignore_list.txt")
        with open(ignore_file, "a", encoding="utf-8") as fh:
            if os.path.isfile(ignore_file) and os.path.getsize(ignore_file) > 0:
                fh.write("\n")
            fh.write(pattern + "\n")

    def _remove_ignore_for_basename(self, basename: str) -> None:
        """Снимает скрытие файла: убирает basename/stem из ``ignore_list``.

        Args:
            basename: Имя файла конфигурации с расширением.
        """
        stem = os.path.splitext(basename)[0]
        ignore_file = os.path.join(self._user_config_dir(), "ignore_list.txt")
        if not os.path.isfile(ignore_file):
            return
        kept = []
        changed = False
        with open(ignore_file, encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if raw and not raw.startswith("#") and raw in (basename, stem):
                    changed = True
                    continue
                kept.append(line if line.endswith("\n") else line + "\n")
        if changed:
            with open(ignore_file, "w", encoding="utf-8") as fh:
                fh.writelines(kept)

    @staticmethod
    def _config_extensions():
        """Допустимые расширения файлов конфигурации.

        Returns:
            Кортеж расширений ``(.txt, .json, .yaml, .yml)``.
        """
        return (".txt", ".json", ".yaml", ".yml")

    def _is_config_file(self, path: str) -> bool:
        """Проверяет, является ли путь файлом конфигурации.

        Args:
            path: Путь к файлу.

        Returns:
            ``True`` для существующего файла с допустимым расширением.
        """
        return os.path.isfile(path) and path.lower().endswith(self._config_extensions())

    def _register_config_file(self, filepath: str, into: dict) -> None:
        """Регистрирует конфиг в словаре, если он не в списке игнорирования.

        Args:
            filepath: Путь к файлу конфигурации.
            into: Словарь ``имя_без_расширения -> путь``.
        """
        base = os.path.basename(filepath)
        ignore_patterns = self._load_config_ignore_patterns()
        if self._is_config_ignored(base, ignore_patterns):
            return
        name = os.path.splitext(base)[0]
        if name not in into:
            into[name] = filepath

    def _scan_config_dir(self, config_dir: str, into: dict) -> None:
        """Сканирует каталог и добавляет найденные конфиги в словарь.

        Args:
            config_dir: Каталог для поиска.
            into: Словарь ``имя -> путь`` для регистрации.
        """
        for ext in ("*.txt", "*.json", "*.yaml", "*.yml"):
            for f in sorted(glob.glob(os.path.join(config_dir, ext))):
                self._register_config_file(f, into)

    def _add_config_file_dialog(self):
        """Открывает диалог выбора файла и добавляет его в список конфигов."""
        path = filedialog.askopenfilename(
            title=self.tr("add_config_file_title"),
            filetypes=[
                ("YAML/JSON", "*.yaml *.yml *.json *.txt"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        if not self._is_config_file(path):
            messagebox.showerror(
                self.tr("input_error_title"),
                self.tr("config_invalid_path").format(path=path),
            )
            return
        try:
            basename = os.path.basename(path)
            self._remove_ignore_for_basename(basename)
            self._append_list_entry(path)
            self.scan_config_files()
            stem = os.path.splitext(basename)[0]
            if stem in self.config_files:
                self.config_combo.set(stem)
                self.on_config_select()
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("config_added").format(path=path),
            )
        except OSError as e:
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("config_add_failed").format(error=str(e)),
            )

    def _remove_config_from_list(self):
        """Удаляет выбранный конфиг из списка и добавляет его в ignore."""
        name = self.config_combo.get().strip()
        if not name or name not in self.config_files:
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("config_nothing_selected")
            )
            return
        if not messagebox.askyesno(
            self.tr("warning_title"),
            self.tr("remove_config_confirm").format(name=name),
        ):
            return
        filepath = os.path.normpath(os.path.abspath(self.config_files[name]))
        basename = os.path.basename(filepath)
        try:
            self._remove_list_entry_path(filepath)
            self._append_ignore_pattern(basename)
            self.scan_config_files()
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("config_removed").format(name=name),
            )
        except OSError as e:
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("config_remove_failed").format(error=str(e)),
            )

    @staticmethod
    def _is_config_ignored(basename: str, patterns) -> bool:
        """Проверяет, нужно ли скрыть файл конфигурации по шаблонам.

        Args:
            basename: Имя файла с расширением.
            patterns: Список glob-шаблонов из ``ignore_list.txt``.

        Returns:
            ``True`` для служебных файлов и совпадений с шаблонами.
        """
        stem = os.path.splitext(basename)[0]
        meta = {
            "extra_paths.txt",
            "ignore_list.txt",
            "list_entries.txt",
        }
        if basename in meta:
            return True
        for pat in patterns:
            if fnmatch.fnmatch(basename, pat) or fnmatch.fnmatch(stem, pat):
                return True
        return False

    def _config_search_dirs(self):
        """Собирает уникальные каталоги для поиска конфигов.

        Returns:
            Список существующих каталогов (основной и extra_paths).
        """
        seen = set()
        dirs = []
        for d in [self.config_dir, *self._load_config_extra_dirs()]:
            d = os.path.normpath(d)
            if d not in seen and os.path.isdir(d):
                seen.add(d)
                dirs.append(d)
        return dirs

    def scan_config_files(self):
        """Обновляет список конфигов в комбобоксе и загружает выбранный по умолчанию."""
        self.config_files.clear()
        current = self.config_combo.get().strip()
        search_dirs = self._config_search_dirs()
        if not search_dirs and not self._load_list_entries():
            messagebox.showwarning(
                self.tr("warning_title"),
                self.tr("config_dir_not_found").format(path=self.config_dir),
            )
            self.config_combo["values"] = []
            return

        for config_dir in search_dirs:
            self._scan_config_dir(config_dir, self.config_files)

        for entry in self._load_list_entries():
            if os.path.isfile(entry):
                if self._is_config_file(entry):
                    self._register_config_file(entry, self.config_files)
            elif os.path.isdir(entry):
                self._scan_config_dir(entry, self.config_files)

        if self.config_files:
            names = sorted(self.config_files.keys(), key=str.lower)
            self.config_combo["values"] = names
            selected = None
            if current and current in self.config_files:
                selected = current
            else:
                for name in names:
                    if name.lower() == "cu":
                        selected = name
                        break
            if selected:
                self.config_combo.set(selected)
                filepath = self.config_files[selected]
                try:
                    config = self.parse_config_file(filepath)
                    self.apply_config(config)
                except Exception as e:
                    messagebox.showerror(
                        self.tr("error_title"),
                        self.tr("failed_load_config").format(error=str(e)),
                    )
            else:
                self.config_combo.set("")
        else:
            self.config_combo["values"] = []
            self.config_combo.set("")

    def on_config_select(self, event=None):
        """Загружает и применяет конфигурацию при выборе в комбобоксе.

        Args:
            event: Событие комбобокса (не используется).
        """
        selected = self.config_combo.get()
        if not selected or selected not in self.config_files:
            return
        filepath = self.config_files[selected]
        try:
            config = self.parse_config_file(filepath)
            self.apply_config(config)
        except Exception as e:
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("failed_load_config").format(error=str(e)),
            )

    def parse_config_file(self, filepath):
        """Разбирает файл конфигурации по расширению (JSON, YAML или текст).

        Args:
            filepath: Путь к файлу конфигурации.

        Returns:
            Словарь параметров кристалла и расчёта.
        """
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".json":
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        elif ext in (".yaml", ".yml"):
            with open(filepath, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            return self.parse_text_config(filepath)

    def parse_text_config(self, filepath):
        """Разбирает текстовый конфиг формата ``ключ: значение``.

        Args:
            filepath: Путь к ``.txt`` файлу конфигурации.

        Returns:
            Словарь параметров.
        """
        config = {}
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("#"):
                i += 1
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key == "atoms" and val.startswith("["):
                    atoms_str = val
                    i += 1
                    while i < len(lines) and not lines[i].strip().endswith("]"):
                        atoms_str += " " + lines[i].strip()
                        i += 1
                    if i < len(lines):
                        atoms_str += " " + lines[i].strip()
                    try:
                        import ast

                        atoms_list = ast.literal_eval(atoms_str)
                        config["atoms"] = atoms_list
                    except (SyntaxError, ValueError):
                        config["atoms"] = atoms_str
                else:
                    config[key] = self._parse_value(val)
            i += 1
        return config

    def _parse_value(self, val):
        """Преобразует строковое значение из текстового конфига в Python-тип.

        Args:
            val: Строка после двоеточия в конфиге.

        Returns:
            ``bool``, ``int``, ``float`` или строка.
        """
        v = val.strip()
        if v.lower() in ("true", "yes", "on"):
            return True
        if v.lower() in ("false", "no", "off"):
            return False
        try:
            if "." in v or "e" in v.lower():
                return float(v)
            else:
                return int(v)
        except ValueError:
            pass
        if v.startswith('"') and v.endswith('"'):
            return v[1:-1]
        if v.startswith("'") and v.endswith("'"):
            return v[1:-1]
        return v

    def _synthesize_cell_params_from_family(self, fam: str | None, config: dict):
        """Дополняет a, b, c, α, β, γ по выбранной сингонии.

        В конфиге можно задать только независимые параметры; остальные
        берутся из ``config`` или текущих виджетов.

        Args:
            fam: Ключ сингонии из ``LATTICE_FAMILY_KEYS`` или ``None``.
            config: Словарь загруженной конфигурации.
        """

        def cfg(key):
            """Читает числовой параметр из конфига по ключу.

            Args:
                key: Имя поля в ``config``.

            Returns:
                Значение как ``float`` или ``None``.
            """
            if key in config and config[key] is not None:
                return float(config[key])
            return None

        def gv(var):
            """Безопасно читает ``float`` из ``DoubleVar``.

            Args:
                var: Переменная tkinter.

            Returns:
                Значение или ``None`` при ``TclError``.
            """
            try:
                return float(var.get())
            except tk.TclError:
                return None

        if not fam or fam == "manual":
            return

        if fam == "cubic":
            side = (
                cfg("a")
                or cfg("b")
                or cfg("c")
                or gv(self.a_var)
                or gv(self.b_var)
                or gv(self.c_var)
            )
            if side is None:
                return
            self.a_var.set(side)
            self.b_var.set(side)
            self.c_var.set(side)
            self.alpha_var.set(90.0)
            self.beta_var.set(90.0)
            self.gamma_var.set(90.0)
            return

        if fam == "tetragonal":
            aa = cfg("a") or cfg("b") or gv(self.a_var) or gv(self.b_var)
            cc = cfg("c") or gv(self.c_var)
            if aa is None or cc is None:
                return
            self.a_var.set(aa)
            self.b_var.set(aa)
            self.c_var.set(cc)
            self.alpha_var.set(90.0)
            self.beta_var.set(90.0)
            self.gamma_var.set(90.0)
            return

        if fam == "orthorhombic":
            a = cfg("a") or gv(self.a_var)
            b = cfg("b") or gv(self.b_var)
            c = cfg("c") or gv(self.c_var)
            if a is None or b is None or c is None:
                return
            self.a_var.set(a)
            self.b_var.set(b)
            self.c_var.set(c)
            self.alpha_var.set(90.0)
            self.beta_var.set(90.0)
            self.gamma_var.set(90.0)
            return

        if fam == "hexagonal":
            aa = cfg("a") or cfg("b") or gv(self.a_var) or gv(self.b_var)
            cc = cfg("c") or gv(self.c_var)
            if aa is None or cc is None:
                return
            self.a_var.set(aa)
            self.b_var.set(aa)
            self.c_var.set(cc)
            self.alpha_var.set(90.0)
            self.beta_var.set(90.0)
            self.gamma_var.set(120.0)
            return

        if fam == "rhombohedral":
            side = (
                cfg("a")
                or cfg("b")
                or cfg("c")
                or gv(self.a_var)
                or gv(self.b_var)
                or gv(self.c_var)
            )
            ang = (
                cfg("alpha")
                or cfg("beta")
                or cfg("gamma")
                or gv(self.alpha_var)
                or gv(self.beta_var)
                or gv(self.gamma_var)
            )
            if side is None or ang is None:
                return
            self.a_var.set(side)
            self.b_var.set(side)
            self.c_var.set(side)
            self.alpha_var.set(ang)
            self.beta_var.set(ang)
            self.gamma_var.set(ang)
            return

        if fam == "monoclinic":
            a = cfg("a") or gv(self.a_var)
            b = cfg("b") or gv(self.b_var)
            c = cfg("c") or gv(self.c_var)
            if a is None or b is None or c is None:
                return
            self.a_var.set(a)
            self.b_var.set(b)
            self.c_var.set(c)
            self.alpha_var.set(90.0)
            self.gamma_var.set(90.0)
            be = cfg("beta")
            if be is not None:
                self.beta_var.set(be)

    def apply_config(self, config):
        """Применяет словарь конфигурации к переменным и виджетам GUI.

        Args:
            config: Параметры кристалла, атомов и расчёта из файла конфигурации.
        """
        if not getattr(self, "_undo_restoring", False):
            self._push_undo_snapshot()
        if "name" in config:
            self.name_var.set(str(config["name"]))

        lf_key = None
        if "lattice_family" in config and config["lattice_family"] is not None:
            lf_key = str(config["lattice_family"]).strip().lower()
        elif "crystal_system" in config and config["crystal_system"] is not None:
            lf_key = str(config["crystal_system"]).strip().lower()
        if lf_key:
            if lf_key in self.LATTICE_FAMILY_KEYS:
                self._set_lattice_family_by_key(lf_key)

        if "a" in config and config["a"] is not None:
            self.a_var.set(float(config["a"]))
        if "b" in config and config["b"] is not None:
            self.b_var.set(float(config["b"]))
        if "c" in config and config["c"] is not None:
            self.c_var.set(float(config["c"]))
        if "alpha" in config and config["alpha"] is not None:
            self.alpha_var.set(float(config["alpha"]))
        if "beta" in config and config["beta"] is not None:
            self.beta_var.set(float(config["beta"]))
        if "gamma" in config and config["gamma"] is not None:
            self.gamma_var.set(float(config["gamma"]))

        self._synthesize_cell_params_from_family(lf_key, config)

        if "space_group" in config:
            if config["space_group"] is None:
                self.space_group_var.set("")
            else:
                self.space_group_var.set(str(int(config["space_group"])))

        if "atoms" in config and isinstance(config["atoms"], list):
            new_atoms = []
            for item in config["atoms"]:
                if len(item) >= 6:
                    atom = {
                        "element": str(item[0]),
                        "x": float(item[1]),
                        "y": float(item[2]),
                        "z": float(item[3]),
                        "occ": float(item[4]),
                        "biso": float(item[5]),
                    }
                    new_atoms.append(atom)
            if new_atoms:
                self.atoms = new_atoms
                self.refresh_atoms_table(self.atoms_frame)

        if "wavelength" in config:
            self.wavelength_var.set(float(config["wavelength"]))
        if "wavelength2" in config and config["wavelength2"] is not None:
            self.wavelength2_var.set(str(float(config["wavelength2"])))
            self.wavelength2_enabled_var.set(True)
        elif "wavelength_2" in config and config["wavelength_2"] is not None:
            self.wavelength2_var.set(str(float(config["wavelength_2"])))
            self.wavelength2_enabled_var.set(True)
        else:
            self.wavelength2_var.set("")
            self.wavelength2_enabled_var.set(False)
        if "wavelength2_intensity_ratio" in config:
            self.wl2_intensity_ratio_var.set(
                float(config["wavelength2_intensity_ratio"])
            )
        elif "wl2_intensity_ratio" in config:
            self.wl2_intensity_ratio_var.set(float(config["wl2_intensity_ratio"]))

        if (
            "twotheta_range" in config
            and isinstance(config["twotheta_range"], list)
            and len(config["twotheta_range"]) == 3
        ):
            self.tth_start_var.set(float(config["twotheta_range"][0]))
            self.tth_end_var.set(float(config["twotheta_range"][1]))
            self.tth_step_var.set(float(config["twotheta_range"][2]))

        if "U" in config:
            self.U_var.set(float(config["U"]))
        if "V" in config:
            self.V_var.set(float(config["V"]))
        if "W" in config:
            self.W_var.set(float(config["W"]))
        if "scale" in config:
            self.scale_var.set(float(config["scale"]))
        if "profile" in config:
            self._set_profile_by_key(str(config["profile"]))
        if "eta" in config:
            self.eta_var.set(float(config["eta"]))
        if "intensity_units" in config:
            self.intensity_units_var.set(str(config["intensity_units"]))
        if "normalize_intensity" in config:
            self.normalize_intensity_var.set(bool(config["normalize_intensity"]))
        if "intensity_max_value" in config:
            self.intensity_max_value_var.set(float(config["intensity_max_value"]))
        if "thetam_deg" in config:
            self.thetam_deg_var.set(float(config["thetam_deg"]))
        if "multiplicity_metric_rtol" in config:
            self.multiplicity_metric_rtol_var.set(
                float(config["multiplicity_metric_rtol"])
            )
        if "multiplicity_metric_atol" in config:
            self.multiplicity_metric_atol_var.set(
                float(config["multiplicity_metric_atol"])
            )
        _bravais_map = {
            "none": "P",
            "p": "P",
            "i": "I",
            "f": "F",
            "c": "C",
            "a": "A",
            "b": "B",
        }
        key = None
        if "bravais_centering" in config and config["bravais_centering"] is not None:
            key = "bravais_centering"
        elif "cubic_bravais" in config and config["cubic_bravais"] is not None:
            key = "cubic_bravais"
        if key is not None:
            v = str(config[key]).strip().lower()
            self.bravais_centering_var.set(_bravais_map.get(v, "P"))
        else:
            self.bravais_centering_var.set("P")

        if getattr(self, "_cell_entries", None):
            self._apply_lattice_constraints()
        self._toggle_wavelength2_fields()
        self._on_profile_selected()
        if not getattr(self, "_undo_restoring", False):
            self._commit_form_state()

    def collect_run_config(self) -> dict:
        """Собирает параметры текущей формы в словарь для YAML."""
        atoms_data = self.collect_atoms_from_widgets()
        if atoms_data is None:
            atoms_data = list(self.atoms)
        atoms = [
            [a["element"], a["x"], a["y"], a["z"], a["occ"], a["biso"]]
            for a in atoms_data
        ]

        sg_text = self.space_group_var.get().strip()
        if sg_text == "" or sg_text.lower() in ("auto", "null", "none"):
            space_group = None
        else:
            space_group = int(sg_text)

        bravais = self.bravais_centering_var.get().strip().lower()
        if bravais in ("", "none", "p"):
            bravais_centering = None
        else:
            bravais_centering = bravais.upper()

        cfg: dict = {
            "name": self.name_var.get().strip(),
            "lattice_family": self._lattice_family_key(),
            "bravais_centering": bravais_centering,
            "space_group": space_group,
            "a": float(self.a_var.get()),
            "b": float(self.b_var.get()),
            "c": float(self.c_var.get()),
            "alpha": float(self.alpha_var.get()),
            "beta": float(self.beta_var.get()),
            "gamma": float(self.gamma_var.get()),
            "atoms": atoms,
            "wavelength": float(self.wavelength_var.get()),
            "twotheta_range": [
                float(self.tth_start_var.get()),
                float(self.tth_end_var.get()),
                float(self.tth_step_var.get()),
            ],
            "U": float(self.U_var.get()),
            "V": float(self.V_var.get()),
            "W": float(self.W_var.get()),
            "scale": float(self.scale_var.get()),
            "profile": self._profile_key(),
            "eta": float(self.eta_var.get()),
            "intensity_units": self.intensity_units_var.get(),
            "normalize_intensity": bool(self.normalize_intensity_var.get()),
            "intensity_max_value": float(self.intensity_max_value_var.get()),
            "thetam_deg": float(self.thetam_deg_var.get()),
            "multiplicity_metric_rtol": float(self.multiplicity_metric_rtol_var.get()),
            "multiplicity_metric_atol": float(self.multiplicity_metric_atol_var.get()),
            "structure_factor_local": bool(self.structure_factor_local),
        }
        if self.wavelength2_enabled_var.get():
            wl2_text = self.wavelength2_var.get().strip()
            if wl2_text:
                cfg["wavelength2"] = float(wl2_text)
                cfg["wavelength2_intensity_ratio"] = float(
                    self.wl2_intensity_ratio_var.get()
                )
        return cfg
