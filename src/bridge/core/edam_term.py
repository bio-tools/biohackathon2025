"""
Module defining the EDAM term data model.
"""

from pydantic import BaseModel, ConfigDict


class EDAMTerm(BaseModel):
    """
    Represent an EDAM term.

    Parameters
    ----------
    iri : str
        The Internationalized Resource Identifier (IRI) of the EDAM term.
    short_form : str
        The short form of the EDAM term (e.g., "format_1930").
    label : str | None
        The preferred label of the EDAM term.
    description : str | None
        The description of the EDAM term, if available.
    narrow_synonym : list[str] | None
        A list of narrow synonyms for the EDAM term, if available.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    iri: str
    short_form: str
    label: str
    description: str | None = None
    narrow_synonym: list[str] | None = None
