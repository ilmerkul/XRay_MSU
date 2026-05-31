import math
import os

import numpy as np


class Atom:
    """Атом в дробных координатах элементарной ячейки."""

    def __init__(self, element, x, y, z, occ, Biso):
        """Создаёт атом с заданными параметрами.

        Args:
            element: Химический символ элемента.
            x: Дробная координата вдоль a.
            y: Дробная координата вдоль b.
            z: Дробная координата вдоль c.
            occ: Кратность занятости (occupancy).
            Biso: Изотропный температурный фактор B_iso (Å²).
        """
        self.element = AtomicScatteringFactor.normalize_element_symbol(element)
        self.frac = np.array([x, y, z])
        self.occ = occ
        self.Biso = Biso


class AtomicScatteringFactor:
    """Таблица атомных факторов рассеяния f₀ (Waas–Kirfel) из файла данных."""

    def __init__(self, filename: str):
        """Загружает таблицу f₀ из текстового файла.

        Args:
            filename: Путь к файлу ``f0_WaasKirf.dat`` или аналогу.

        Raises:
            FileNotFoundError: Если файл не существует.
            ValueError: Если файл — указатель Git LFS или не распознан.
        """
        self.data = {}
        self._normalized_index = {}
        self._parse(filename)

    @staticmethod
    def normalize_element_symbol(symbol: str) -> str:
        """Нормализует символ элемента к виду ``Na``, ``Cl`` и т.п.

        Args:
            symbol: Строка с символом элемента (возможны пробелы и BOM).

        Returns:
            Нормализованный символ или пустая строка для пустого ввода.
        """
        s = str(symbol).strip().replace("\ufeff", "").replace("\u200b", "")
        if not s:
            return s
        return s[:1].upper() + s[1:].lower()

    def _parse(self, filename):
        """Разбирает файл таблицы f₀ и заполняет ``self.data``.

        Args:
            filename: Путь к файлу таблицы.

        Raises:
            FileNotFoundError: Если файл не найден.
            ValueError: Если файл — Git LFS или не содержит распознанных записей.
        """
        path = str(filename)
        if not path or not os.path.isfile(path):
            raise FileNotFoundError(f"Файл атомных факторов не найден: {path}")

        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        if lines and lines[0].startswith("version https://git-lfs.github.com/spec/v1"):
            raise ValueError(
                f"Файл {path} — указатель Git LFS, а не таблица f₀. "
                "Выполните: git lfs pull"
            )

        i = 0
        n = len(lines)
        while i < n:
            line = lines[i].strip()
            if line.startswith("#S"):
                parts = line.split(maxsplit=2)
                if len(parts) < 3:
                    i += 1
                    continue
                symbol = parts[2].strip()

                i += 1
                while i < n:
                    data_line = lines[i].strip()
                    if data_line and not data_line.startswith("#"):
                        tokens = data_line.split()
                        if len(tokens) == 11:
                            a = list(map(float, tokens[:5]))
                            c = float(tokens[5])
                            b = list(map(float, tokens[6:]))
                            self.data[symbol] = (a, b, c)
                            norm = self.normalize_element_symbol(symbol)
                            self._normalized_index[norm] = symbol
                        break
                    i += 1
                i += 1
            else:
                i += 1

        if not self.data:
            raise ValueError(f"Файл атомных факторов пуст или не распознан: {path}")

    def get_f0(self, symbol, k):
        """Вычисляет f₀ для заданного волнового вектора k = sin(θ)/λ.

        Args:
            symbol: Символ элемента.
            k: Модуль волнового вектора (Å⁻¹).

        Returns:
            Значение атомного фактора f₀.

        Raises:
            ValueError: Если символ не найден в таблице.
        """
        raw_symbol = str(symbol).strip()
        resolved = None
        if raw_symbol in self.data:
            resolved = raw_symbol
        else:
            normalized = self.normalize_element_symbol(raw_symbol)
            resolved = self._normalized_index.get(normalized)
            if resolved is None:
                raw_low = raw_symbol.lower()
                for key in self.data:
                    if key.lower() == raw_low:
                        resolved = key
                        break
        if resolved is None:
            raise ValueError(f"Символ '{raw_symbol}' не найден в данных.")
        a, b, c = self.data[resolved]
        k2 = k * k
        result = c
        for i in range(5):
            result += a[i] * math.exp(-b[i] * k2)
        return result

    def get_f0_from_theta_lambda(self, symbol, theta_deg, lambda_ang):
        """Вычисляет f₀ по углу Брэгга и длине волны.

        Args:
            symbol: Символ элемента.
            theta_deg: Угол Брэгга в градусах.
            lambda_ang: Длина волны в ångström.

        Returns:
            Значение атомного фактора f₀.
        """
        theta_rad = math.radians(theta_deg)
        k = math.sin(theta_rad) / lambda_ang
        return self.get_f0(symbol, k)

    def available_symbols(self):
        """Возвращает список символов элементов, доступных в таблице.

        Returns:
            Список строк-символов в порядке загрузки из файла.
        """
        return list(self.data.keys())
