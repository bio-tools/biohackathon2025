"""
Module defining the SPDX license data model.
"""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


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
    order : int | None
        The order of the cross-reference.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    url: HttpUrl
    isValid: bool | None = None
    isLive: bool | None = None
    isWayBackLink: bool | None = None
    match_: str | None = Field(default=None, alias="match")
    timestamp: str | None = None
    order: int | None = None


class SPDXLicense(BaseModel):
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
    licenseTextHtml : str
        HTML-formatted license text.
    isDeprecatedLicenseId : bool | None
        Whether the license ID is deprecated.
    standardLicenseTemplate : str | None
        Standard license template text, if available.
    isOsiApproved : bool | None
        Whether the license is OSI-approved.
    isFsfLibre : bool | None
        Whether the license is FSF libre.
    seeAlso : list[HttpUrl] | None
        List of URLs with additional information about the license.
    crossRef : list[SPDXCrossRef] | None
        List of cross-references for the license.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    licenseId: str
    name: str
    licenseText: str
    licenseTextHtml: str

    isDeprecatedLicenseId: bool | None = None
    standardLicenseTemplate: str | None = None
    isOsiApproved: bool | None = None
    isFsfLibre: bool | None = None

    seeAlso: list[HttpUrl] | None = None
    crossRef: list[SPDXCrossRef] | None = None
