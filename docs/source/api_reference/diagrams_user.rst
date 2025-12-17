user-facing bridge process diagrams (for GitHub ⇄ bio.tools)
============================================================

The sequence diagram below shows how the bridge is invoked via the

- command-line interface (CLI),
- REST API, or
- Python package

to synchronize metadata between a GitHub repository and a bio.tools record.

In the **GitHub → bio.tools direction**,
repository metadata is retrieved from GitHub, optionally combined with existing bio.tools metadata,
and processed by an internal pipeline to produce a bio.tools–compliant metadata record.

In the reverse **bio.tools → GitHub direction**,
metadata is fetched from bio.tools and used to determine repository updates,
resulting in a GitHub pull request and, optionally, issues creation.

*Internal pipeline components are abstracted to emphasize the user-level interaction and high-level data flow.*

.. mermaid:: _process_diagrams/user_diagram.mmd

TBD
=====