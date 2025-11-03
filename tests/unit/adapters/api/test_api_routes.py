"""
Tests for API route registration and availability.
"""

from fastapi.testclient import TestClient

from bridge.adapters.api import app

client = TestClient(app)


def test_docs_available():
    """
    Test that the /docs endpoint is available.

    Raises
    ------
    AssertionError
        If the /docs endpoint is not available (status code is not 200).
    """
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_github_to_biotools_endpoint_exists():
    """
    Test that the /github-to-biotools endpoint is available.

    Raises
    ------
    AssertionError
        If the /github-to-biotools endpoint is not available
        (status code is not 201 or 500).
    """
    resp = client.post("/github-to-biotools", json={"owner": "o", "repo": "r", "biotools_id": None})
    # handler will likely fail deeper (because of mocked bootstrap etc.), so just assert route shape:
    assert resp.status_code in (201, 500)


def test_biotools_to_github_endpoint_exists():
    """
    Test that the /biotools-to-github endpoint is available.

    Raises
    ------
    AssertionError
        If the /biotools-to-github endpoint is not available
        (status code is not 201 or 500).
    """
    resp = client.post(
        "/biotools-to-github",
        json={"biotools_id": "tool", "owner": "o", "repo": "r"},
    )
    assert resp.status_code in (201, 500)
