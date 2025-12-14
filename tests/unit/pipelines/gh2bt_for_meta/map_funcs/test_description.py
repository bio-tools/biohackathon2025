"""
Unit tests for mapping GitHub description to bio.tools description (map_description).
"""

from __future__ import annotations

import pytest

import bridge.pipelines.gh2bt_for_meta.map_funcs.description as mod


pytestmark = pytest.mark.asyncio


class _Resp:
    def __init__(self, content: str):
        self.content = content


class _FakeHF:
    def __init__(self, content: str | None = None, raise_exc: Exception | None = None):
        self._content = content
        self._raise = raise_exc
        self.calls = []

    async def generate(self, messages):
        self.calls.append(messages)
        if self._raise is not None:
            raise self._raise
        return _Resp(self._content or "")


@pytest.mark.parametrize(
    "gh_params, bt_description, expected",
    [
        # 1) GitHub params absent => preserve bt
        (None, None, None),
        (None, "Keep me", "Keep me"),
        # 2) GitHub description present => overwrite / set after normalize_text
        ({"description": "New desc"}, None, "New desc"),
        ({"description": "New desc"}, "Old desc", "New desc"),
        # 3) GitHub description present but effectively identical => preserve bt
        ({"description": "Same."}, "Same", "Same"),
        ({"description": "Same   "}, "Same.", "Same."),
        ({"description": "Same.\n"}, "Same", "Same"),
        # 4) GitHub provides empty-ish description => treated as no description, preserve bt (if bt exists)
        ({"description": None}, "BT desc", "BT desc"),
        ({"description": ""}, "BT desc", "BT desc"),
        ({"description": "   \n\t"}, "BT desc", "BT desc"),
    ],
)
async def test_map_description_github_and_preserve_cases(monkeypatch, gh_params, bt_description, expected):
    # Keep deterministic normalization; we only need basic behavior here.
    monkeypatch.setattr(mod, "normalize_text", lambda s: None if s is None or str(s).strip() == "" else str(s).strip())

    out = await mod.map_description(gh_params=gh_params, bt_description=bt_description)
    assert out == expected


async def test_map_description_no_gh_desc_no_bt_no_readme_returns_none(monkeypatch):
    monkeypatch.setattr(mod, "normalize_text", lambda s: None if s is None or str(s).strip() == "" else str(s).strip())

    out = await mod.map_description(gh_params={"description": None, "readme": None}, bt_description=None)
    assert out is None


async def test_map_description_llm_used_when_no_gh_desc_and_no_bt_and_readme_present(monkeypatch):
    """
    LLM is called only when:
      - gh_description is None/empty after normalize_text
      - bt_description is None
      - readme exists
    Result is normalize_text(response.content).strip()[:999]
    """
    monkeypatch.setattr(mod, "normalize_text", lambda s: None if s is None or str(s).strip() == "" else str(s).strip())

    fake = _FakeHF(content="  A tool that does X.\nSecond sentence.   ")
    monkeypatch.setattr(mod, "HuggingFaceProvider", lambda: fake)

    out = await mod.map_description(
        gh_params={"description": None, "readme": "README content\n" * 3},
        bt_description=None,
    )

    assert out == "A tool that does X.\nSecond sentence."
    assert len(fake.calls) == 1

    # Sanity: it builds 2 messages (system + user prompt)
    messages = fake.calls[0]
    assert len(messages) == 2
    assert getattr(messages[0], "role", None) == "system"
    assert getattr(messages[1], "role", None) == "user"


async def test_map_description_llm_failure_returns_none_and_does_not_overwrite_bt(monkeypatch):
    monkeypatch.setattr(mod, "normalize_text", lambda s: None if s is None or str(s).strip() == "" else str(s).strip())

    fake = _FakeHF(raise_exc=RuntimeError("boom"))
    monkeypatch.setattr(mod, "HuggingFaceProvider", lambda: fake)

    out = await mod.map_description(
        gh_params={"description": None, "readme": "Some readme"},
        bt_description=None,
    )
    assert out is None
    assert len(fake.calls) == 1

    # If bt_description exists, failure must not matter (LLM shouldn't be called at all)
    out2 = await mod.map_description(
        gh_params={"description": None, "readme": "Some readme"},
        bt_description="Existing BT",
    )
    assert out2 == "Existing BT"
    assert len(fake.calls) == 1  # still only the first call


async def test_map_description_readme_is_truncated_in_prompt(monkeypatch):
    """
    The prompt includes readme.strip()[:MAX_README_CHARS]. We verify the user message
    content does not exceed that slice (plus prompt boilerplate).
    """
    monkeypatch.setattr(mod, "normalize_text", lambda s: None if s is None or str(s).strip() == "" else str(s).strip())

    fake = _FakeHF(content="desc")
    monkeypatch.setattr(mod, "HuggingFaceProvider", lambda: fake)

    readme = "A" * (mod.MAX_README_CHARS + 500)
    await mod.map_description(
        gh_params={"description": None, "readme": readme},
        bt_description=None,
    )

    user_msg = fake.calls[0][1]
    user_content = user_msg.content

    # The readme excerpt should be exactly MAX_README_CHARS long inside the prompt.
    assert ("A" * mod.MAX_README_CHARS) in user_content
    assert ("A" * (mod.MAX_README_CHARS + 1)) not in user_content


async def test_map_description_llm_output_is_capped_to_999_chars(monkeypatch):
    monkeypatch.setattr(mod, "normalize_text", lambda s: None if s is None or str(s).strip() == "" else str(s).strip())

    long = "x" * 1500
    fake = _FakeHF(content=long)
    monkeypatch.setattr(mod, "HuggingFaceProvider", lambda: fake)

    out = await mod.map_description(
        gh_params={"description": None, "readme": "short"},
        bt_description=None,
    )

    assert out is not None
    assert len(out) == 999
    assert out == ("x" * 999)
