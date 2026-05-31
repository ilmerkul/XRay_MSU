"""Тесты CLI: поиск конфигов и разрешение путей."""

from pathlib import Path

import pytest

from src.cli import DEFAULT_CONFIG, _resolve_config_path, discover_config_files


def test_discover_config_files_includes_alpha_fe():
    names = [name for name, _ in discover_config_files()]
    assert Path(DEFAULT_CONFIG).name in names


def test_resolve_config_path_by_basename():
    path = _resolve_config_path("alpha-Fe.yaml")
    assert Path(path).is_file()
    assert Path(path).name == "alpha-Fe.yaml"


def test_resolve_config_path_relative():
    path = _resolve_config_path(DEFAULT_CONFIG)
    assert Path(path).is_file()


def test_resolve_config_path_missing():
    with pytest.raises(FileNotFoundError, match="не найден"):
        _resolve_config_path("no-such-config-xyz.yaml")
