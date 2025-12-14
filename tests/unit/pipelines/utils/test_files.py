"""
Unit tests for basic file utilities.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bridge.pipelines.utils.files import (
    check_file_with_extension_exists,
    get_file_content,
    load_dict_from_yaml_file,
)


# ----------------------------
# check_file_with_extension_exists
# ----------------------------


def test_check_file_with_extension_exists_true_for_nested_file(tmp_path: Path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir(parents=True, exist_ok=True)
    (tmp_path / "a" / "b" / "readme.md").write_text("# hi", encoding="utf-8")

    assert check_file_with_extension_exists(str(tmp_path), ".md") is True


def test_check_file_with_extension_exists_false_when_no_match(tmp_path: Path):
    (tmp_path / "file.txt").write_text("x", encoding="utf-8")

    assert check_file_with_extension_exists(str(tmp_path), ".md") is False


def test_check_file_with_extension_exists_false_for_empty_dir(tmp_path: Path):
    assert check_file_with_extension_exists(str(tmp_path), ".md") is False


def test_check_file_with_extension_exists_respects_dot_in_extension(tmp_path: Path):
    (tmp_path / "filemd").write_text("x", encoding="utf-8")  # no ".md"
    (tmp_path / "file.md").write_text("x", encoding="utf-8")  # has ".md"

    assert check_file_with_extension_exists(str(tmp_path), ".md") is True


# ----------------------------
# get_file_content
# ----------------------------


def test_get_file_content_returns_none_when_missing(tmp_path: Path):
    missing = tmp_path / "missing.txt"
    assert get_file_content(missing) is None


def test_get_file_content_reads_utf8_text(tmp_path: Path):
    p = tmp_path / "hello.txt"
    p.write_text("héllo\n", encoding="utf-8")

    assert get_file_content(p) == "héllo\n"


def test_get_file_content_accepts_str_path(tmp_path: Path):
    p = tmp_path / "hello.txt"
    p.write_text("ok", encoding="utf-8")

    assert get_file_content(str(p)) == "ok"


# ----------------------------
# load_dict_from_yaml_file
# ----------------------------


def test_load_dict_from_yaml_file_returns_empty_dict_when_missing(tmp_path: Path):
    missing = tmp_path / "missing.yaml"
    assert load_dict_from_yaml_file(missing) == {}


def test_load_dict_from_yaml_file_returns_empty_dict_when_empty_file(tmp_path: Path):
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")

    assert load_dict_from_yaml_file(p) == {}


def test_load_dict_from_yaml_file_parses_valid_yaml_dict(tmp_path: Path):
    p = tmp_path / "data.yaml"
    p.write_text("a: 1\nb: two\n", encoding="utf-8")

    assert load_dict_from_yaml_file(p) == {"a": 1, "b": "two"}


def test_load_dict_from_yaml_file_returns_empty_dict_when_yaml_is_invalid(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text("a: [1, 2\n", encoding="utf-8")  # missing closing bracket

    assert load_dict_from_yaml_file(p) == {}


def test_load_dict_from_yaml_file_returns_empty_dict_when_yaml_is_not_a_mapping(tmp_path: Path):
    # safe_load can return a list/scalar; current function contract says dict or {}
    p = tmp_path / "list.yaml"
    p.write_text("- a\n- b\n", encoding="utf-8")

    out = load_dict_from_yaml_file(p)
    assert isinstance(out, dict)
    assert out == {}


def test_load_dict_from_yaml_file_calls_safe_load_and_handles_yamlerror(tmp_path: Path, monkeypatch):
    p = tmp_path / "data.yaml"
    p.write_text("a: 1\n", encoding="utf-8")

    def boom(_content):
        raise yaml.YAMLError("nope")

    monkeypatch.setattr(yaml, "safe_load", boom)

    assert load_dict_from_yaml_file(p) == {}
