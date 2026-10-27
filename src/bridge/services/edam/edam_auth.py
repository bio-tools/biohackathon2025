"""
Helper for constructing EMBL-EBI OLS4 API request headers.
"""


def get_edam_headers() -> dict:
    """
    Construct headers for EMBL-EBI OLS4 API requests.

    Returns
    -------
    dict
        A dictionary containing the accept header.
    """
    return {"Accept": "application/json"}
