"""
Unit tests for bridge.services.huggingface.HuggingFaceProvider.
"""

import pytest

from bridge.services.huggingface import HuggingFaceProvider
from bridge.services.protocols import ChatMessage


@pytest.mark.asyncio
async def test_hf_provider_generate_happy(monkeypatch):
    """
    Test happy path of HuggingFaceProvider.generate.

    Raises
    ------
    AssertionError
        If the generated message does not match expected values.
    """

    class FakeChoiceMsg:
        role = "assistant"
        content = "hello"

    class FakeChoice:
        message = FakeChoiceMsg()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeChat:
        def __init__(self):
            self.completions = self

        def create(self, *a, **k):
            return FakeResponse()

    class FakeClient:
        def __init__(self, *a, **k):
            self.chat = FakeChat()

    # patch the client constructor
    monkeypatch.setattr("bridge.services.huggingface.huggingface_provider.InferenceClient", FakeClient)

    prov = HuggingFaceProvider(model="dummy/model", provider="auto")
    out = await prov.generate([ChatMessage(role="user", content="hi")])
    assert out.role == "assistant"
    assert out.content == "hello"


@pytest.mark.asyncio
async def test_hf_provider_generate_empty(monkeypatch):
    """
    Test HuggingFaceProvider.generate with empty messages.

    Raises
    ------
    ValueError
        If the input messages list is empty.
    """
    # still patch client so __init__ doesn't fail
    monkeypatch.setattr(
        "bridge.services.huggingface.huggingface_provider.InferenceClient",
        lambda *a, **k: None,
    )
    prov = HuggingFaceProvider(model="dummy/model", provider="auto")
    with pytest.raises(ValueError, match="cannot be empty"):
        await prov.generate([])
