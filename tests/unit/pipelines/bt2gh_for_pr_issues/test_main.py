from __future__ import annotations

from types import SimpleNamespace

import pytest

import bridge.pipelines.bt2gh_for_pr_issues.main as mod


pytestmark = pytest.mark.asyncio


# -----------------------------
# Helpers
# -----------------------------


class _Runner:
    def __init__(self, value):
        self._value = value
        self.calls = 0

    async def run(self):
        self.calls += 1
        return self._value


def _args(*, existing_repo_model, metadata_model, repo_path="/tmp/repo"):
    """
    Deliberately NOT constructing BiotoolsToGitHubForPRPipelineArgs (Pydantic),
    because these unit tests target pipeline behavior, not input validation.
    """
    return SimpleNamespace(
        existing_repo_model=existing_repo_model,
        metadata_model=metadata_model,
        repo_path=repo_path,
    )


# -----------------------------
# Fixtures
# -----------------------------


@pytest.fixture()
def patch_destination(monkeypatch):
    """
    Patch MapDestination so we control which mapping keys are requested.
    """

    class _Dest:
        issue = ["issue_a", "issue_b"]
        pr = ["pr_a", "pr_b"]

    monkeypatch.setattr(mod, "MapDestination", lambda: _Dest())
    return _Dest


@pytest.fixture()
def patch_mapper(monkeypatch):
    """
    Patch MapBioTools2GitHub to a controllable stub that exposes `.map`.
    Also capture init args so we can assert wiring.

    Important: create `state["map"]` immediately so tests can populate it
    before `run()` instantiates the mapper.
    """
    state = {
        "repo": None,
        "metadata": None,
        "repo_path": None,
        "map": {},  # <-- available immediately
    }

    class _Mapper:
        def __init__(self, *, repo, metadata, repo_path):
            state["repo"] = repo
            state["metadata"] = metadata
            state["repo_path"] = repo_path

        @property
        def map(self):
            return state["map"]

    monkeypatch.setattr(mod, "MapBioTools2GitHub", _Mapper)
    return state


# -----------------------------
# Tests
# -----------------------------


async def test_run_wires_models_and_path_into_mapper_and_merges_outputs(patch_mapper, patch_destination):
    repo = object()
    metadata = SimpleNamespace(name="ToolName")  # used only for logging; not asserted

    patch_mapper["map"].update(
        {
            # issues
            "issue_a": _Runner({"Issue A": "Body A"}),
            "issue_b": _Runner({"Issue B": "Body B"}),
            # prs
            "pr_a": _Runner({"README.md": "new readme"}),
            "pr_b": _Runner({"CITATION.cff": "new cff"}),
        }
    )

    file_changes, issues = await mod.run(_args(existing_repo_model=repo, metadata_model=metadata, repo_path="/x/repo"))

    # wiring into mapper
    assert patch_mapper["repo"] is repo
    assert patch_mapper["metadata"] is metadata
    assert patch_mapper["repo_path"] == "/x/repo"

    # merged outputs
    assert issues == {"Issue A": "Body A", "Issue B": "Body B"}
    assert file_changes == {"README.md": "new readme", "CITATION.cff": "new cff"}


async def test_run_skips_falsy_map_results(patch_mapper, patch_destination):
    repo = object()
    metadata = SimpleNamespace(name="ToolName")

    patch_mapper["map"].update(
        {
            "issue_a": _Runner(None),
            "issue_b": _Runner({}),
            "pr_a": _Runner(None),
            "pr_b": _Runner({}),
        }
    )

    file_changes, issues = await mod.run(_args(existing_repo_model=repo, metadata_model=metadata))

    assert issues == {}
    assert file_changes == {}


async def test_run_calls_each_destination_key_exactly_once(patch_mapper, patch_destination):
    repo = object()
    metadata = SimpleNamespace(name="ToolName")

    issue_a = _Runner({"I": "A"})
    issue_b = _Runner({"J": "B"})
    pr_a = _Runner({"f1": "x"})
    pr_b = _Runner({"f2": "y"})

    patch_mapper["map"].update(
        {
            "issue_a": issue_a,
            "issue_b": issue_b,
            "pr_a": pr_a,
            "pr_b": pr_b,
        }
    )

    await mod.run(_args(existing_repo_model=repo, metadata_model=metadata))

    assert issue_a.calls == 1
    assert issue_b.calls == 1
    assert pr_a.calls == 1
    assert pr_b.calls == 1


async def test_run_merges_with_last_write_wins_on_duplicate_keys(patch_mapper, patch_destination):
    """
    Pipeline uses dict union-update (`|=`). Later values override earlier ones.
    """
    repo = object()
    metadata = SimpleNamespace(name="ToolName")

    patch_mapper["map"].update(
        {
            "issue_a": _Runner({"Same title": "old"}),
            "issue_b": _Runner({"Same title": "new"}),
            "pr_a": _Runner({"README.md": "old"}),
            "pr_b": _Runner({"README.md": "new"}),
        }
    )

    file_changes, issues = await mod.run(_args(existing_repo_model=repo, metadata_model=metadata))

    assert issues == {"Same title": "new"}
    assert file_changes == {"README.md": "new"}
