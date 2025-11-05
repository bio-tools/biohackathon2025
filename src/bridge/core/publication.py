"""
Module defining the Publication data model.
"""

from pydantic import BaseModel, ConfigDict


class Author(BaseModel):
    """
    Represent an author of a publication.

    Parameters
    ----------
    first_name : str | None
        The first name of the author.
    last_name : str | None
        The last name of the author.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    first_name: str | None
    last_name: str | None
    name: str | None


class Publication(BaseModel):
    """
    Represent a publication.

    Parameters
    ----------
    doi : str | None
        The Digital Object Identifier (DOI) of the publication.
    title : str | None
        The title of the publication.
    authors : list[str] | None
        The list of authors of the publication.
    year : int | None
        The publication year.
    journal : str | None
        The journal in which the publication appeared.
    volume : str | None
        The volume of the journal.
    issue : str | None
        The issue of the journal.
    page_start : int | None
        The starting page number of the publication.
    page_end : int | None
        The ending page number of the publication.
    pub_type : str | None
        The type of publication (e.g., "article").
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    doi: str | None

    title: str | None
    authors: list[Author] | None
    year: int | None

    journal: str | None
    volume: str | None
    issue: str | None
    page_start: int | None
    page_end: int | None

    pub_type: str | None = "article"
