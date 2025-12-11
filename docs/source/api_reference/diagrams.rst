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

The diagram below details the process of composing the metadata models
from GitHub repositories and bio.tools entries.

.. mermaid:: sequence/composing.mmd


GitHub → bio.tools pipeline
----------------------------

The diagram below details the pipeline for mapping GitHub repository
to a bio.tools tool metadata.

.. mermaid:: sequence/gh2bt.mmd