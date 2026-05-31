#!/usr/bin/env python3
"""Переводит \\(…\\) / \\[…\\] в $…$ / $$…$$ для pandoc → PDF (кириллица + xelatex)."""

import pathlib
import sys


def convert(text: str) -> str:
    """Преобразует \\(…\\) и \\[…\\] в $…$ и $$…$$ для pandoc.

    Блоки кода в тройных backticks не изменяются.

    Args:
        text: Исходный Markdown-текст.

    Returns:
        Текст с формулами в синтаксисе pandoc/LaTeX.
    """
    result = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("```", i):
            end = text.find("```", i + 3)
            if end < 0:
                result.append(text[i:])
                break
            result.append(text[i : end + 3])
            i = end + 3
            continue
        if text.startswith(r"\(", i):
            j = text.find(r"\)", i + 2)
            if j >= 0:
                result.extend(["$", text[i + 2 : j], "$"])
                i = j + 2
                continue
        if text.startswith(r"\[", i):
            j = text.find(r"\]", i + 2)
            if j >= 0:
                result.extend(["\n$$\n", text[i + 2 : j].strip(), "\n$$\n"])
                i = j + 2
                continue
        result.append(text[i])
        i += 1
    return "".join(result)


def main() -> None:
    """Читает файл из argv[1] и выводит преобразованный текст в stdout."""
    path = pathlib.Path(sys.argv[1])
    sys.stdout.write(convert(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
