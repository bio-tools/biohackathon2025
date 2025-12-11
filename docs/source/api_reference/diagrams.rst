bridge diagrams
=================

General flow of the GitHub ⇄ bio.tools bridge
----------------------------------------------

This sequence diagram illustrates the high-level runtime flow of the GitHub ⇄ bio.tools bridge.
It shows how user input is handled by the interface, routed through the central handler, and executed
depending on the selected direction of the bridge.

.. mermaid:: sequence/bridge-flow.mmd


Composing models
-----------------

The sequence diagram below details the process of composing the metadata models
from GitHub repositories and bio.tools entries.

.. mermaid:: sequence/composing.mmd


GitHub → bio.tools pipeline
----------------------------

The sequence diagram below details the pipeline for mapping GitHub repository
to a bio.tools tool metadata.

.. mermaid:: sequence/gh2bt.mmd


bio.tools → GitHub pipeline
----------------------------

The sequence diagram below details the pipeline for mapping a bio.tools tool
metadata to a GitHub repository in the form of a pull request and, optionally,
issues.

.. mermaid:: sequence/bt2gh.mmd