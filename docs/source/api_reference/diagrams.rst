bridge process diagrams (for GitHub ⇄ bio.tools)
=================================================

General flow of the GitHub ⇄ bio.tools bridge
----------------------------------------------

This sequence diagram illustrates the high-level runtime flow of the GitHub ⇄ bio.tools bridge.
It shows how user input is handled by the interface, routed through the central handler, and executed
depending on the selected direction of the bridge.

.. mermaid:: _process_diagrams/bridge-flow.mmd


Composing models
-----------------

The sequence diagram below details the process of composing the metadata models
from GitHub repositories and bio.tools entries.

.. mermaid:: _process_diagrams/composing.mmd


GitHub → bio.tools pipeline
----------------------------

The sequence diagram below details the pipeline for mapping GitHub repository
to a bio.tools tool metadata.

.. mermaid:: _process_diagrams/gh2bt.mmd


GitHub → bio.tools mapping
----------------------------

The flowcharts below detail the mapping of specific fields from GitHub to bio.tools.

Map description
~~~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/description.mmd

Map version
~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/version.mmd

Map maturity
~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/maturity.mmd

Map publications
~~~~~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/publication.mmd

Map documentation
~~~~~~~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/documentation.mmd

Map biotools ID
~~~~~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/biotools_id.mmd

Map name
~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/name.mmd

Map homepage
~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/homepage.mmd

Map language
~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/language.mmd

Map license
~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/license.mmd

Policy: GitHub over bio.tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/gh2bt/policy-gh-over-bt.mmd


bio.tools → GitHub pipeline
----------------------------

The sequence diagram below details the pipeline for mapping a bio.tools tool
metadata to a GitHub repository in the form of a pull request and, optionally,
issues.

.. mermaid:: _process_diagrams/bt2gh.mmd


bio.tools → GitHub mapping for issues
---------------------------------------

The flowcharts below detail the mapping of specific fields from bio.tools to GitHub
in the form of issues.

Map description
~~~~~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/bt2gh/description.mmd

Map homepage
~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/bt2gh/homepage.mmd

Map topics
~~~~~~~~~~~

.. mermaid:: _process_diagrams/bt2gh/topics.mmd

Map version
~~~~~~~~~~~~~~

TODO: add diagram here.


bio.tools → GitHub mapping for pull requests
---------------------------------------------

The flowcharts below detail the mapping of specific fields from bio.tools to GitHub
in the form of pull requests.

Map name
~~~~~~~~~~

TODO: add diagram here.

Map license
~~~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/bt2gh/license.mmd

Map citation
~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/bt2gh/citation.mmd

Map readme
~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/bt2gh/readme.mmd


Policy: bio.tools over GitHub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/bt2gh/policy-bt-over-gh.mmd

Policy: bio.tools on top of GitHub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. mermaid:: _process_diagrams/bt2gh/policy-bt-ontop-gh.mmd
