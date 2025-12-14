"""
Unit tests for mapping bio.tools EDAM annotations to GitHub topics (map_topics).

These tests focus on the public function `map_topics` (not private helpers).
They validate:
- bt_edam is None => no issue
- bt_edam provides no usable terms => no issue
- gh topics missing some/all bt terms => issue proposed with correct body bits
- normalization effects (spaces -> hyphens, case-folding, punctuation stripping)
- singular vs plural phrasing
"""

from __future__ import annotations

import pytest

from bridge.pipelines.bt2gh_for_pr_issues.map_funcs.topics import map_topics

TITLE = "Add EDAM annotations from bio.tools metadata"


# ---------------------------------------------------------------------
# Minimal "model-like" stubs (avoid depending on pydantic models in tests)
# ---------------------------------------------------------------------
class _TermObj:
    def __init__(self, term: str | None):
        self.term = term


class _IOObj:
    def __init__(self, data_term: str | None = None, format_terms: list[str] | None = None):
        self.data = _TermObj(data_term) if data_term is not None else None
        self.format = [_TermObj(t) for t in (format_terms or [])]


class _FunctionItem:
    def __init__(
        self,
        operation_terms: list[str] | None = None,
        inputs: list[_IOObj] | None = None,
        outputs: list[_IOObj] | None = None,
    ):
        self.operation = [_TermObj(t) for t in (operation_terms or [])]
        self.input = inputs or []
        self.output = outputs or []


class _TopicItem:
    def __init__(self, term: str | None):
        self.term = term


def _body(out: dict[str, str] | None) -> str:
    assert out is not None
    assert list(out.keys()) == [TITLE]
    return out[TITLE]


def _missing_terms_from_body(body: str) -> set[str]:
    """
    Pull the missing term list from the body. The implementation prints them
    as a newline-separated block between two blank lines.
    """
    marker = "not included in the GitHub topics:\n\n"
    assert marker in body
    after = body.split(marker, 1)[1]
    terms_block = after.split("\n\nPlease consider", 1)[0]
    return {line.strip() for line in terms_block.splitlines() if line.strip()}


@pytest.mark.parametrize(
    "gh_topics, bt_edam, expect_issue, expected_missing",
    [
        # -----------------------------
        # bio.tools silent => no issue
        # -----------------------------
        (None, None, False, set()),
        (["a"], None, False, set()),
        # -----------------------------
        # bt_edam present but no usable terms => no issue
        # -----------------------------
        ([], {"topics": [], "functions": []}, False, set()),
        (["x"], {"topics": [_TopicItem(None)], "functions": []}, False, set()),
        # function list exists but contains no terms anywhere
        (["x"], {"topics": [], "functions": [_FunctionItem()]}, False, set()),
        # -----------------------------
        # missing one term => singular wording + one term in body
        # -----------------------------
        (
            ["already-there"],
            {"topics": [_TopicItem("Sequence analysis")], "functions": []},
            True,
            {"sequence-analysis"},
        ),
        # -----------------------------
        # missing multiple terms from topics + function flattening
        # -----------------------------
        (
            ["sequence-analysis"],
            {
                "topics": [_TopicItem("Sequence analysis"), _TopicItem("Data visualisation")],
                "functions": [
                    _FunctionItem(
                        operation_terms=["Read mapping"],
                        inputs=[_IOObj(data_term="Sequence", format_terms=["FASTA"])],
                        outputs=[_IOObj(data_term="Alignment", format_terms=["SAM"])],
                    )
                ],
            },
            True,
            {
                # topic terms:
                "data-visualisation",
                # function terms:
                "read-mapping",
                "sequence",
                "fasta",
                "alignment",
                "sam",
            },
        ),
        # -----------------------------
        # normalization: punctuation stripped/collapsed, case-folding, spaces to hyphens
        # -----------------------------
        (
            ["protein-sequences", "rna-seq"],
            {
                "topics": [
                    _TopicItem("Protein sequences"),
                    _TopicItem("RNA-seq!!"),  # punctuation => hyphen collapse => "rna-seq"
                    _TopicItem(
                        "  Weird   Term "
                    ),  # multiple spaces => hyphens then collapse => "weird---term" -> "weird-term"
                ],
                "functions": [],
            },
            True,
            {"weird-term"},  # the other two already present after normalization
        ),
        # -----------------------------
        # gh_topics None treated as empty => all bt terms missing
        # -----------------------------
        (
            None,
            {"topics": [_TopicItem("Metagenomics")], "functions": []},
            True,
            {"metagenomics"},
        ),
    ],
)
def test_map_topics_issue_creation_and_missing_set(gh_topics, bt_edam, expect_issue, expected_missing):
    out = map_topics(gh_topics=gh_topics, bt_edam=bt_edam)

    if not expect_issue:
        assert out is None
        return

    body = _body(out)
    missing = _missing_terms_from_body(body)
    assert missing == set(expected_missing)


@pytest.mark.parametrize(
    "missing_terms, expected_bits",
    [
        (
            {"one-term"},
            [
                "contain 1 EDAM term that is not included",
                "Please consider adding it to the GitHub repository.",
                "--add-topic one-term",
                '"one-term"',
            ],
        ),
        (
            {"a", "b"},
            [
                "contain 2 EDAM terms that are not included",
                "Please consider adding them to the GitHub repository.",
                "--add-topic a",
                "--add-topic b",
                '"a","b"',  # JSON payload in body (sorted)
            ],
        ),
    ],
)
def test_map_topics_body_singular_plural_and_commands(missing_terms, expected_bits):
    # drive missing terms by giving empty gh topics and bt_edam producing exactly those terms
    bt_edam = {"topics": [_TopicItem(t.replace("-", " ")) for t in missing_terms], "functions": []}
    out = map_topics(gh_topics=[], bt_edam=bt_edam)
    body = _body(out)

    for bit in expected_bits:
        assert bit in body


def test_map_topics_does_not_duplicate_terms_when_topics_and_functions_overlap():
    bt_edam = {
        "topics": [_TopicItem("Sequence analysis")],
        "functions": [
            _FunctionItem(operation_terms=["Sequence analysis"]),  # same after normalization
        ],
    }
    out = map_topics(gh_topics=[], bt_edam=bt_edam)
    body = _body(out)

    missing = _missing_terms_from_body(body)
    assert missing == {"sequence-analysis"}  # only once
    assert "contain 1 EDAM term" in body
