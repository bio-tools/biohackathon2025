# """
# Unit tests for mapping bio.tools function EDAM terms to GitHub topics.
# """

# import pytest

# from bridge.core.biotools import EDAMdata, EDAMformat, FunctionItem, InputItem, OperationItem, OutputItem
# from bridge.pipelines.bt2gh_for_pr_issues.map_funcs.function import _flatten_function, map_function2topics


# @pytest.fixture
# def sample_function_item():
#     """
#     bio.tools FunctionItem for testing.
#     """
#     return FunctionItem(
#         operation=[OperationItem(term="Multiple sequence alignment")],
#         input=[InputItem(data=EDAMdata(term="DNA sequence"), format=[EDAMformat(term="FASTA")])],
#         output=[OutputItem(data=EDAMdata(term="Sequence alignment"), format=[EDAMformat(term="ClustalW format")])],
#     )


# def test_flatten_function_basic(sample_function_item):
#     """
#     Test merging all EDAM terms into flat list
#     """
#     result = _flatten_function([sample_function_item])
#     assert isinstance(result, list)
#     assert "multiple-sequence-alignment" in result
#     assert "dna-sequence" in result
#     assert "fasta" in result
#     assert "sequence-alignment" in result
#     assert "clustalw-format" in result


# def test_flatten_function_empty():
#     """
#     Test merging all EDAM terms into flat list when list is empty
#     """
#     result = _flatten_function([])
#     assert result == []


# def test_map_function2topics_missing_terms(sample_function_item):
#     """
#     Test EDAM term missing in GitHub topics
#     """
#     gh_topics = ["dna-sequence"]
#     result = map_function2topics(gh_topics, [sample_function_item])
#     assert isinstance(result, dict)
#     assert "Add function annotations from bio.tools metadata" in result
#     assert "multiple-sequence-alignment" in result["Add function annotations from bio.tools metadata"]


# def test_map_function2topics_all_present(sample_function_item):
#     """
#     Test all EDAM terms are present in GitHub topics
#     """
#     gh_topics = ["multiple-sequence-alignment", "dna-sequence", "fasta", "sequence-alignment", "clustalw-format"]
#     result = map_function2topics(gh_topics, [sample_function_item])
#     assert result is None


# def test_map_function2topics_none_function():
#     """
#     Test bio.tools functions is None
#     """
#     result = map_function2topics(["topic"], None)
#     assert result is None
