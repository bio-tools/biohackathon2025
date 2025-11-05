"""
Helper for constructing Europe PMC API request headers.
"""


def get_europe_pmc_headers() -> dict:
    """
    Construct headers for Europe PMC API requests.

    Returns
    -------
    dict
        A dictionary containing the accept header.
    """
    return {"Accept": "application/json"}
