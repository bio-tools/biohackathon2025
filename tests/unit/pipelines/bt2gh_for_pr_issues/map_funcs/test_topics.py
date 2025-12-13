"""
Unit tests for mapping function map bio.tools EDAM annotations to GitHub topics.
"""

import pytest

from bridge.pipelines.bt2gh_for_pr_issues.map_funcs.topics import (
    _flatten_function,
    _normalize_edam_term,
    map_topics,
)


# ----------------------------
# Minimal stubs (only attributes used by the code)
# ----------------------------


class _Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _topic(term: str | None):
    return _Obj(term=term)


def _op(term: str | None):
    return _Obj(term=term)


def _data(term: str | None):
    return _Obj(term=term)


def _format(term: str | None):
    return _Obj(term=term)


def _io_item(data_term: str | None = None, format_terms: list[str] | None = None):
    return _Obj(
        data=_data(data_term) if data_term is not None else None,
        format=[_format(t) for t in (format_terms or [])],
    )


def _fn_item(
    *,
    op_terms: list[str] | None = None,
    input_data_term: str | None = None,
    input_format_terms: list[str] | None = None,
    output_data_term: str | None = None,
    output_format_terms: list[str] | None = None,
):
    return _Obj(
        operation=[_op(t) for t in (op_terms or [])],
        input=[_io_item(input_data_term, input_format_terms)] if (input_data_term or input_format_terms) else [],
        output=[_io_item(output_data_term, output_format_terms)] if (output_data_term or output_format_terms) else [],
    )


# ----------------------------
# Helper tests: normalization
# ----------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        # spaces -> hyphens, lowercase
        ("Sequence alignment", "sequence-alignment"),
        # punctuation -> hyphens, collapse multiple hyphens
        ("Gene/Protein (ID)", "gene-protein-id"),
        # preserve existing hyphens and lowercase
        ("RNA-Seq", "rna-seq"),
        # strip leading/trailing whitespace
        ("  Leading and trailing  ", "leading-and-trailing"),
    ],
)
def test_normalize_edam_term(raw, expected):
    assert _normalize_edam_term(raw) == expected


# ----------------------------
# Helper tests: flattening
# ----------------------------


def test_flatten_function_empty_returns_empty_list():
    assert _flatten_function([]) == []
    assert _flatten_function(None) == []  # type: ignore[arg-type]


def test_flatten_function_collects_operation_input_output_terms():
    fn = _fn_item(
        op_terms=["Sequence alignment"],
        input_data_term="Sequence data",
        input_format_terms=["FASTA"],
        output_data_term="Alignment",
        output_format_terms=["Clustal"],
    )

    flat = _flatten_function([fn])

    assert "Sequence alignment" in flat
    assert "Sequence data" in flat
    assert "FASTA" in flat
    assert "Alignment" in flat
    assert "Clustal" in flat


def test_flatten_function_ignores_missing_terms_gracefully():
    fn = _Obj(
        operation=[_op(None), _op("Something")],
        input=[_Obj(data=None, format=[_format(None), _format("TXT")])],
        output=[_Obj(data=_data(None), format=None)],
    )

    assert _flatten_function([fn]) == ["Something", "TXT"]


# ----------------------------
# Main tests: map_topics
# ----------------------------


@pytest.mark.parametrize(
    "gh_topics, bt_edam, expected_issue, must_contain, must_not_contain",
    [
        # Case 1: No bio.tools EDAM input -> no issue
        (["genomics"], None, False, [], []),
        # Case 2: No missing terms -> no issue
        (
            ["proteomics", "sequence-alignment"],
            {"topics": [_topic("Proteomics")], "functions": [_fn_item(op_terms=["Sequence alignment"])]},
            False,
            [],
            [],
        ),
        # Case 3: Missing terms -> issue includes both normalized terms + CLI hints
        (
            ["genomics"],
            {"topics": [_topic("Proteomics")], "functions": [_fn_item(op_terms=["Sequence alignment"])]},
            True,
            ["proteomics", "sequence-alignment", "--add-topic proteomics", "--add-topic sequence-alignment"],
            [],
        ),
        # Case 4: Case-insensitive match on GH topics -> no issue
        (
            ["Proteomics"],
            {"topics": [_topic("proteomics")], "functions": []},
            False,
            [],
            [],
        ),
        # Case 5: Weird term normalization: one matches GH, one missing -> issue only for missing
        (
            ["gene-protein-id"],
            {"topics": [_topic("Gene/Protein (ID)")], "functions": [_fn_item(op_terms=["RNA-Seq"])]},
            True,
            ["rna-seq", "--add-topic rna-seq"],
            ["gene-protein-id"],  # should not be in missing list
        ),
        # Case 6: No existing GH topics (None) -> treat as empty and create issue
        (
            None,
            {"topics": [_topic("Proteomics")], "functions": []},
            True,
            ["proteomics", "--add-topic proteomics"],
            [],
        ),
    ],
)
def test_map_topics(gh_topics, bt_edam, expected_issue, must_contain, must_not_contain):
    """
    Test map_topics issue proposal behavior.
    """
    result = map_topics(gh_topics, bt_edam)

    if not expected_issue:
        assert result is None
        return

    assert result is not None
    assert list(result.keys()) == ["Add EDAM annotations from bio.tools metadata"]

    body = result["Add EDAM annotations from bio.tools metadata"]
    for s in must_contain:
        assert s in body
    for s in must_not_contain:
        assert s not in body


def test_map_topics_deduplicates_terms_across_topics_and_functions():
    """
    Same term appears in both bio.tools topic and function -> should only be proposed once.
    """
    result = map_topics(
        gh_topics=[],
        bt_edam={"topics": [_topic("Proteomics")], "functions": [_fn_item(op_terms=["Proteomics"])]},
    )

    assert result is not None
    body = result["Add EDAM annotations from bio.tools metadata"]

    # CLI suggestion should include the term only once
    assert body.count("--add-topic proteomics") == 1
