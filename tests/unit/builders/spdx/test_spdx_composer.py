"""
Unit tests for compose_spdx_license_metadata.

Public behavior covered:
- wires SPDXLicenseIngestor -> SPDXLicenseTransformer and returns transformed model
- passes spdx_id into ingestor constructor
- propagates exceptions from ingestion/transformation (no logging assertions)
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

# Adjust import to your actual module path
import bridge.builders.spdx.spdx_composer as mod


# -----------------------------
# Stubs
# -----------------------------


@dataclass
class _SPDXLicense:
    licenseId: str
    licenseText: str | None = None


class _DummyIngestor:
    def __init__(self, spdx_id: str):
        self.spdx_id = spdx_id


class _DummyTransformer:
    def __init__(self, ingestor):
        self.ingestor = ingestor
        self.transform_calls = 0

    async def transform(self):
        self.transform_calls += 1
        return _SPDXLicense(licenseId=self.ingestor.spdx_id, licenseText="text")


# -----------------------------
# Tests
# -----------------------------


@pytest.mark.asyncio
async def test_compose_spdx_license_metadata_wires_ingestor_and_transformer(monkeypatch):
    created = {}

    def _ingestor_factory(*, spdx_id: str):
        created["spdx_id"] = spdx_id
        ing = _DummyIngestor(spdx_id=spdx_id)
        created["ingestor"] = ing
        return ing

    def _transformer_factory(ingestor):
        tr = _DummyTransformer(ingestor)
        created["transformer"] = tr
        return tr

    monkeypatch.setattr(mod, "SPDXLicenseIngestor", _ingestor_factory)
    monkeypatch.setattr(mod, "SPDXLicenseTransformer", _transformer_factory)
    monkeypatch.setattr(mod, "SPDXLicense", _SPDXLicense)  # typing only; safe

    out = await mod.compose_spdx_license_metadata("MIT")

    assert created["spdx_id"] == "MIT"
    assert created["ingestor"].spdx_id == "MIT"
    assert created["transformer"].ingestor is created["ingestor"]
    assert created["transformer"].transform_calls == 1
    assert isinstance(out, _SPDXLicense)
    assert out.licenseId == "MIT"
    assert out.licenseText == "text"


@pytest.mark.asyncio
async def test_compose_spdx_license_metadata_propagates_transform_errors(monkeypatch):
    class _BoomTransformer:
        def __init__(self, ingestor):
            self.ingestor = ingestor

        async def transform(self):
            raise RuntimeError("kaboom")

    monkeypatch.setattr(mod, "SPDXLicenseIngestor", lambda *, spdx_id: _DummyIngestor(spdx_id))
    monkeypatch.setattr(mod, "SPDXLicenseTransformer", lambda ing: _BoomTransformer(ing))

    with pytest.raises(RuntimeError, match="kaboom"):
        await mod.compose_spdx_license_metadata("MIT")
