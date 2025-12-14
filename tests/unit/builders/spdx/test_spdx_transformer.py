"""
Unit tests for SPDXLicenseTransformer.

Covers:
- transform() calls ingestor.fetch() and constructs SPDXLicense from raw data
- propagates validation errors from SPDXLicense model
- does not assert on logging
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

# Adjust import to your actual module path
import bridge.builders.spdx.spdx_transormer as mod


# -----------------------------
# Minimal stubs
# -----------------------------


@dataclass
class _SPDXLicense:
    licenseId: str
    name: str | None = None
    licenseText: str | None = None


class _DummyIngestor:
    def __init__(self, spdx_id: str, payload: dict):
        self.spdx_id = spdx_id
        self._payload = payload
        self.fetch_calls = 0

    async def fetch(self) -> dict:
        self.fetch_calls += 1
        return self._payload


@pytest.fixture()
def patch_model(monkeypatch):
    """
    Patch transformer module's SPDXLicense symbol to a small dataclass,
    so tests don't depend on generated Pydantic schema details.
    """
    monkeypatch.setattr(mod, "SPDXLicense", _SPDXLicense)


# -----------------------------
# Tests
# -----------------------------


@pytest.mark.asyncio
async def test_transform_builds_spdx_license_from_raw(patch_model):
    payload = {
        "licenseId": "MIT",
        "name": "MIT License",
        "licenseText": "Permission is hereby granted...",
    }
    ing = _DummyIngestor(spdx_id="MIT", payload=payload)
    t = mod.SPDXLicenseTransformer(ingestor=ing)

    out = await t.transform()

    assert ing.fetch_calls == 1
    assert isinstance(out, _SPDXLicense)
    assert out.licenseId == "MIT"
    assert out.name == "MIT License"
    assert out.licenseText.startswith("Permission")


@pytest.mark.asyncio
async def test_transform_passes_through_extra_fields_when_model_allows(patch_model):
    """
    With the stub dataclass, extra fields are not accepted by default,
    so we only check that transformer forwards raw_data into constructor.
    """
    payload = {"licenseId": "Apache-2.0", "name": "Apache License 2.0"}
    ing = _DummyIngestor(spdx_id="Apache-2.0", payload=payload)
    t = mod.SPDXLicenseTransformer(ingestor=ing)

    out = await t.transform()
    assert out.licenseId == "Apache-2.0"
    assert out.name == "Apache License 2.0"


@pytest.mark.asyncio
async def test_transform_raises_when_required_fields_missing(patch_model):
    """
    Missing required field should raise (dataclass __init__ TypeError),
    mirroring the "fail fast" behavior you'd also get from Pydantic validation.
    """
    payload = {"name": "MIT License"}  # missing licenseId
    ing = _DummyIngestor(spdx_id="MIT", payload=payload)
    t = mod.SPDXLicenseTransformer(ingestor=ing)

    with pytest.raises(TypeError):
        await t.transform()
