"""
Mapping GitHub topics to bio.tools EDAM topics.

This module aligns GitHub repository topics with bio.tools EDAM topics.
It compares the list of topics reported by GitHub for a repository with the list of
existing bio.tools EDAM topics and applies a reconciliation policy that prefers GitHub
topics when they are present, while retaining existing bio.tools topics.
"""

from bridge.builders import compose_edam_term_metadata
from bridge.core import EDAMTerm
from bridge.core.biotools import TopicItem
from bridge.logging import get_user_logger
from bridge.pipelines.policies.gh2bt import reconcile_gh_ontop_bt

logger = get_user_logger()


def _to_topic_set_gh(gh_topics: list[str] | None) -> set[str] | None:
    """
    Normalize GitHub topics to a lowercased string set.

    Parameters
    ----------
    gh_topics : list[str] | None
        List of GitHub topics, or ``None`` if no topics are present.

    Returns
    -------
    set[str] | None
        A set of lowercased GitHub topic names, or ``None`` if no topics are provided.
    """
    if not gh_topics:
        return None
    return {topic.lower() for topic in gh_topics}


def _to_topic_set_bt(bt_topics: list[TopicItem] | None) -> set[str] | None:
    """
    Normalize bio.tools EDAM topics to a lowercased string set.

    Parameters
    ----------
    bt_topics : list[TopicItem] | None
        List of bio.tools EDAM topic annotations, or ``None`` if no topics are recorded.

    Returns
    -------
    set[str] | None
        A set of lowercased topic names derived from the `TopicItem` values, or ``None`` if no topics are recorded.
    """
    if not bt_topics:
        return None
    return {topic.term.lower() for topic in bt_topics}


async def _cast_to_biotools_topics(topics: set[str]) -> list[TopicItem] | None:
    """
    Cast a set of topic strings to a list of EDAM topics by looking up corresponding EDAM terms.

    Parameters
    ----------
    topics : set[str]
        A set of lowercased topic names.

    Returns
    -------
    list[TopicItem] | None
        A list of `TopicItem` enum members corresponding to the input topic names,
        or ``None`` if no valid topics are found.
    """
    bt_topics: list[TopicItem] = []
    for topic in topics:
        try:
            edam_term: EDAMTerm = await compose_edam_term_metadata(topic)
            if not edam_term or not edam_term.label or not edam_term.iri:
                logger.note(f"GitHub topic '{topic}' could not be resolved to a valid EDAM term and will be skipped.")
                continue
            matched_topic = TopicItem(term=edam_term.label, uri=edam_term.iri)
            logger.added(
                f"Mapped GitHub topic '{topic}' to bio.tools EDAM topic "
                f"'{matched_topic.term}' with URI '{matched_topic.uri}'.",
            )
            bt_topics.append(matched_topic)
        except Exception as e:
            logger.note(f"Error retrieving EDAM term for GitHub topic '{topic}': {e}. This topic will be skipped.")
            continue

    return bt_topics or None


async def map_topics(gh_topics: list[str] | None, bt_topics: list[TopicItem] | None) -> list[TopicItem] | None:
    """
    Map and reconcile GitHub topics with bio.tools EDAM topics using the generic GitHub-over-bio.tools policy.

    GitHub topics are normalized to a lowercased set of strings, and bio.tools topics are similarly normalized
    to a set of lowercased topic names derived from the `TopicItem` enum members.

    Parameters
    ----------
    gh_topics : list[str] | None
        List of GitHub topics, or ``None`` if no topics are present.
    bt_topics : list[TopicItem] | None
        List of existing bio.tools EDAM topic annotations, or ``None`` if no topics are recorded.

    Returns
    -------
    list[TopicItem] | None
        A reconciled list of `TopicItem` enum members representing the topics for the tool,
        preferring GitHub topics when available, or ``None`` if no topics can be determined
    """
    gh_norm = _to_topic_set_gh(gh_topics)
    bt_norm = _to_topic_set_bt(bt_topics)

    return await reconcile_gh_ontop_bt(
        gh_norm=gh_norm,
        bt_norm=bt_norm,
        bt_value=bt_topics,
        build_bt_from_gh=None,
        build_bt_from_norm=lambda bt_norm: _cast_to_biotools_topics(bt_norm),
        log_label="topics",
    )
