"""
Module defining the SPDX license data model.
"""

from pydantic import BaseModel, Field, HttpUrl


class SPDXCrossRef(BaseModel):
    """
    Represent a cross-reference for an SPDX license.

    Parameters
    ----------
    url : HttpUrl
        The URL of the cross-reference.
    isValid : bool | None
        Whether the cross-reference is valid.
    isLive : bool | None
        Whether the cross-reference is live.
    isWayBackLink : bool | None
        Whether the cross-reference is a Wayback Machine link.
    match_ : str | None
        The match type of the cross-reference.
    timestamp : str | None
        The timestamp of the cross-reference.
    """

    url: HttpUrl
    isValid: bool | None = None
    isLive: bool | None = None
    isWayBackLink: bool | None = None
    match_: str | None = Field(default=None, alias="match")
    timestamp: str | None = None


class SPDXLicenseModel(BaseModel):
    """
    Represent an SPDX license.

    Parameters
    ----------
    licenseId : str
        SPDX license identifier (e.g. ``"MIT"``, ``"GPL-3.0-only"``).
    name : str
        Full name of the license.
    licenseText : str
        Canonical license text.
    isOsiApproved : bool | None
        Whether the license is OSI approved.
    isFsfLibre : bool | None
        Whether the license is FSF libre.
    standardLicenseHeader : str | None
        Standard license header text, if available.
    licenseComments : str | None
        Additional comments about the license.
    seeAlso : list[HttpUrl] | None
        List of URLs with more information about the license.
    crossRef : list[SPDXCrossRef] | None
        List of cross-references for the license.
    """

    licenseId: str
    name: str
    licenseText: str

    isOsiApproved: bool | None = None
    isFsfLibre: bool | None = None
    standardLicenseHeader: str | None = None
    licenseComments: str | None = None

    seeAlso: list[HttpUrl] | None = None
    crossRef: list[SPDXCrossRef] | None = None
