"""
Unit tests for compose_europe_pmc_metadata.

Public behavior covered:
- wires EuropePMCIngestor(pmid/pmcid/doi) into EuropePMCTransformer and returns transformed model
- passes through kwargs exactly (including None)
- propagates exceptions from transformer/ingestion (no logging assertions)
- uses the first non-None identifier for "ID" only in logs (we don't test logging)
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

# Adjust import to your actual module path
import bridge.builders.europe_pmc.europe_pmc_composer as mod


# -----------------------------
# Stubs
# -----------------------------


@dataclass
class _Publication:
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None


class _DummyIngestor:
    def __init__(self, *, pmid=None, pmcid=None, doi=None):
        self.pmid = pmid
        self.pmcid = pmcid
        self.doi = doi


class _DummyTransformer:
    def __init__(self, ingestor):
        self.ingestor = ingestor
        self.transform_calls = 0

    async def transform(self):
        self.transform_calls += 1
        return _Publication(doi=self.ingestor.doi, pmid=self.ingestor.pmid, pmcid=self.ingestor.pmcid)


# -----------------------------
# Tests
# -----------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pmid, pmcid, doi",
    [
        ("123", None, None),
        (None, "PMC999", None),
        (None, None, "10.1000/xyz"),
        ("123", "PMC999", "10.1000/xyz"),  # all provided: we still pass all through
        (None, None, None),  # allowed by current function signature/logic
    ],
)
async def test_compose_europe_pmc_metadata_wires_ingestor_and_transformer(monkeypatch, pmid, pmcid, doi):
    created = {}

    def _ingestor_factory(*, pmid=None, pmcid=None, doi=None):
        ing = _DummyIngestor(pmid=pmid, pmcid=pmcid, doi=doi)
        created["ingestor"] = ing
        return ing

    def _transformer_factory(ingestor):
        tr = _DummyTransformer(ingestor)
        created["transformer"] = tr
        return tr

    monkeypatch.setattr(mod, "EuropePMCIngestor", _ingestor_factory)
    monkeypatch.setattr(mod, "EuropePMCTransformer", _transformer_factory)
    monkeypatch.setattr(mod, "Publication", _Publication)  # typing only; safe

    out = await mod.compose_europe_pmc_metadata(pmid=pmid, pmcid=pmcid, doi=doi)

    assert created["ingestor"].pmid == pmid
    assert created["ingestor"].pmcid == pmcid
    assert created["ingestor"].doi == doi
    assert created["transformer"].ingestor is created["ingestor"]
    assert created["transformer"].transform_calls == 1

    assert isinstance(out, _Publication)
    assert (out.pmid, out.pmcid, out.doi) == (pmid, pmcid, doi)


@pytest.mark.asyncio
async def test_compose_europe_pmc_metadata_propagates_transform_errors(monkeypatch):
    class _BoomTransformer:
        def __init__(self, ingestor):
            self.ingestor = ingestor

        async def transform(self):
            raise RuntimeError("kaboom")

    monkeypatch.setattr(mod, "EuropePMCIngestor", lambda **kw: _DummyIngestor(**kw))
    monkeypatch.setattr(mod, "EuropePMCTransformer", lambda ing: _BoomTransformer(ing))

    with pytest.raises(RuntimeError, match="kaboom"):
        await mod.compose_europe_pmc_metadata(doi="10.1000/xyz")
