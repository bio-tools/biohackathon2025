"""
Unit tests for compose_biotools_metadata.

Public behavior covered:
- require_args enforces "identifier"
- wires BiotoolsIngestor(identifier) -> BiotoolsToolTransformer -> transform()
- returns the transformed model
- propagates exceptions from transformer/ingestion (no logging assertions)
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

# Adjust import to your actual module path
import bridge.builders.biotools.biotools_composer as mod


# -----------------------------
# Stubs
# -----------------------------


@dataclass
class _BioToolsModel:
    biotoolsID: str


class _DummyIngestor:
    def __init__(self, biotools_id: str):
        self.biotools_id = biotools_id


class _DummyTransformer:
    def __init__(self, ingestor):
        self.ingestor = ingestor
        self.calls = 0

    async def transform(self):
        self.calls += 1
        return _BioToolsModel(biotoolsID=self.ingestor.biotools_id)


# -----------------------------
# Tests
# -----------------------------


@pytest.mark.asyncio
async def test_compose_biotools_metadata_wires_ingestor_and_transformer(monkeypatch):
    created = {}

    def _ingestor_factory(biotools_id: str):
        ing = _DummyIngestor(biotools_id)
        created["ingestor"] = ing
        return ing

    def _transformer_factory(ingestor):
        tr = _DummyTransformer(ingestor)
        created["transformer"] = tr
        return tr

    monkeypatch.setattr(mod, "BiotoolsIngestor", _ingestor_factory)
    monkeypatch.setattr(mod, "BiotoolsToolTransformer", _transformer_factory)
    monkeypatch.setattr(mod, "BiotoolsToolModel", _BioToolsModel)  # typing only

    out = await mod.compose_biotools_metadata(identifier="toolid")

    assert created["ingestor"].biotools_id == "toolid"
    assert created["transformer"].ingestor is created["ingestor"]
    assert created["transformer"].calls == 1

    assert isinstance(out, _BioToolsModel)
    assert out.biotoolsID == "toolid"


@pytest.mark.asyncio
async def test_compose_biotools_metadata_propagates_transform_errors(monkeypatch):
    class _BoomTransformer:
        def __init__(self, ingestor):
            self.ingestor = ingestor

        async def transform(self):
            raise RuntimeError("kaboom")

    monkeypatch.setattr(mod, "BiotoolsIngestor", lambda biotools_id: _DummyIngestor(biotools_id))
    monkeypatch.setattr(mod, "BiotoolsToolTransformer", lambda ing: _BoomTransformer(ing))

    with pytest.raises(RuntimeError, match="kaboom"):
        await mod.compose_biotools_metadata(identifier="toolid")


@pytest.mark.asyncio
async def test_compose_biotools_metadata_requires_identifier():
    with pytest.raises(ValueError, match=r"Missing required args: identifier"):
        await mod.compose_biotools_metadata()
