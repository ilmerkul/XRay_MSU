"""Пути и каталоги frozen-режима (без реального PyInstaller)."""

from pathlib import Path

from src.runtime_layout import _ensure_extra_paths_lists_runs


def test_extra_paths_adds_runs(tmp_path: Path):
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "extra_paths.txt").write_text("# comment only\n", encoding="utf-8")
    _ensure_extra_paths_lists_runs(cfg)
    text = (cfg / "extra_paths.txt").read_text(encoding="utf-8")
    assert "runs" in text.split()
