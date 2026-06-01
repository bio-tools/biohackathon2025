"""
Mapping GitHub topics to bio.tools EDAM topics.
"""

from bridge.core.biotools import TopicItem
from bridge.logging import get_user_logger

logger = get_user_logger()


def map_topics(gh_topics: list[str] | None, bt_topics: list[TopicItem] | None) -> list[TopicItem] | None:
    """
    Map GitHub topics to bio.tools EDAM topics.
    """
    pass
