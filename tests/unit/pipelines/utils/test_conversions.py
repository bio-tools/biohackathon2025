"""
Unit tests for conversion utilities (enums, SVG base64, object->primitive).
"""

from __future__ import annotations

import base64
from enum import Enum

import pytest
from pydantic import BaseModel

from bridge.pipelines.utils.conversions import find_matching_enum_member, object_to_primitive, svg_to_base64


# ----------------------------
# Fixtures / helpers
# ----------------------------


class _License(Enum):
    MIT = "MIT"
    Apache_2_0 = "Apache-2.0"
    GPL_3_0 = "GPL-3.0"


class _InnerModel(BaseModel):
    name: str
    flag: bool | None = None


class _OuterModel(BaseModel):
    inner: _InnerModel
    tags: list[str] | None = None
    license: _License | None = None
    count: int | None = None


# ----------------------------
# find_matching_enum_member
# ----------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        # Match on member.value (case-insensitive)
        ("mit", _License.MIT),
        ("MIT", _License.MIT),
        ("Apache-2.0", _License.Apache_2_0),
        ("gpl-3.0", _License.GPL_3_0),
        # Match on member.name (case-insensitive)
        ("apache_2_0", _License.Apache_2_0),
        ("GPL_3_0", _License.GPL_3_0),
        # No match
        ("bsd-3-clause", None),
        ("not-a-real-license", None),
    ],
)
def test_find_matching_enum_member(value, expected):
    assert find_matching_enum_member(value, _License) == expected


# ----------------------------
# svg_to_base64
# ----------------------------


def test_svg_to_base64_raises_if_missing(tmp_path):
    missing = tmp_path / "nope.svg"
    with pytest.raises(FileNotFoundError):
        svg_to_base64(str(missing))


def test_svg_to_base64_strips_xml_decl_and_comments_and_whitespace(tmp_path):
    svg = tmp_path / "icon.svg"
    svg.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!-- comment -->
<svg>
  <g>
    <path d="M0 0"/>
  </g>
</svg>
""",
        encoding="utf-8",
    )

    b64 = svg_to_base64(str(svg))
    assert "\n" not in b64  # function promises no newlines

    decoded = base64.b64decode(b64).decode("utf-8")
    assert decoded.startswith("<svg>")  # XML decl removed
    assert "<!--" not in decoded  # comments stripped
    assert ">\n<" not in decoded  # whitespace between tags collapsed
    assert decoded.endswith("</svg>")


# ----------------------------
# object_to_primitive
# ----------------------------


def test_object_to_primitive_passthrough_primitives():
    assert object_to_primitive("x") == "x"
    assert object_to_primitive(1) == 1
    assert object_to_primitive(1.5) == 1.5
    assert object_to_primitive(True) is True
    assert object_to_primitive(None) is None


def test_object_to_primitive_converts_enum_to_value():
    assert object_to_primitive(_License.MIT) == "MIT"


def test_object_to_primitive_converts_containers_recursively():
    payload = {
        "license": _License.Apache_2_0,
        "items": (_License.GPL_3_0, {"x": _License.MIT}),
        "set": {_License.MIT, _License.Apache_2_0},
    }

    out = object_to_primitive(payload)

    assert out["license"] == "Apache-2.0"
    assert out["items"][0] == "GPL-3.0"
    assert out["items"][1]["x"] == "MIT"
    assert sorted(out["set"]) == ["Apache-2.0", "MIT"]


def test_object_to_primitive_converts_pydantic_models_and_excludes_none_fields():
    m = _OuterModel(
        inner=_InnerModel(name="tool", flag=None),
        tags=None,
        license=_License.MIT,
        count=None,
    )

    out = object_to_primitive(m)

    # Top-level is a dict
    assert isinstance(out, dict)

    # None fields excluded by model_dump(exclude_none=True)
    assert "tags" not in out
    assert "count" not in out

    # Nested model converted
    assert out["inner"] == {"name": "tool"}

    # Enum converted to value
    assert out["license"] == "MIT"
