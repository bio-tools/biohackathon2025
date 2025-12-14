"""
Unit tests for BiotoolsToolTransformer.
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

# Adjust to your real module path
import bridge.builders.biotools.biotools_transformer as mod


pytestmark = pytest.mark.asyncio


# -----------------------------
# Minimal stubs (avoid pydantic / generated model requirements)
# -----------------------------


@dataclass
class _BiotoolsToolModel:
    raw: dict

    def __init__(self, **kwargs):
        # behave like a model: store all received fields
        self.raw = dict(kwargs)


class _DummyIngestor:
    def __init__(self, biotools_id: str, payload: dict):
        self.biotools_id = biotools_id
        self._payload = payload
        self.fetch_calls = 0

    async def fetch(self) -> dict:
        self.fetch_calls += 1
        return self._payload


@pytest.fixture()
def patch_model(monkeypatch):
    """
    Patch the transformer module to use a tiny stub instead of the generated model.
    """
    monkeypatch.setattr(mod, "BiotoolsToolModel", _BiotoolsToolModel)


# -----------------------------
# Tests
# -----------------------------


async def test_transform_calls_fetch_and_constructs_model(patch_model):
    payload = {
        "biotoolsID": {"root": "tool-id"},
        "name": "Tool Name",
        "description": "A sufficiently long description",
        "homepage": {"root": "https://example.org"},
    }
    ing = _DummyIngestor("tool-id", payload)
    tr = mod.BiotoolsToolTransformer(ingestor=ing)

    out = await tr.transform()

    assert ing.fetch_calls == 1
    assert isinstance(out, _BiotoolsToolModel)
    assert out.raw == payload


@pytest.mark.parametrize(
    "payload",
    [
        {},  # empty dict should still call model ctor
        {"name": "Only name"},  # partial dict passthrough
        {"biotoolsID": "tool-id", "topic": ["Genomics"]},
    ],
)
async def test_transform_passthrough_various_payloads(patch_model, payload):
    ing = _DummyIngestor("tool-id", payload)
    tr = mod.BiotoolsToolTransformer(ingestor=ing)

    out = await tr.transform()

    assert ing.fetch_calls == 1
    assert out.raw == payload


async def test_transform_propagates_model_constructor_errors(monkeypatch):
    class _FailingModel:
        def __init__(self, **kwargs):
            raise ValueError("boom")

    monkeypatch.setattr(mod, "BiotoolsToolModel", _FailingModel)

    ing = _DummyIngestor("tool-id", {"x": 1})
    tr = mod.BiotoolsToolTransformer(ingestor=ing)

    with pytest.raises(ValueError, match="boom"):
        await tr.transform()
