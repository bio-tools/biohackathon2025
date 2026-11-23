# Bidirectional bridge: GitHub ⇄ bio.tools

[![PyPI](https://img.shields.io/pypi/v/metadata-bridge)](https://pypi.org/project/metadata-bridge/)
[![Tests](https://github.com/bio-tools/metadata-bridge/actions/workflows/tests.yml/badge.svg?branch=dev)](https://github.com/bio-tools/metadata-bridge/actions/workflows/tests.yml)
[![Docs](https://github.com/bio-tools/metadata-bridge/actions/workflows/docs.yml/badge.svg?branch=dev)](https://bio-tools.github.io/metadata-bridge/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](https://github.com/bio-tools/metadata-bridge/blob/dev/LICENSE.txt)

**Goal**: 
make software metadata painless. 
This tool extracts high-quality metadata from GitHub repos 
to build bio.tools entries
and uses bio.tools records to propose improvements back to GitHub 
(badges, descriptions, files). 
It currently targets GitHub and bio.tools, 
but the architecture is intentionally pluggable for more backends later.

**Why**:
- Reduces manual work in software metadata curation.
- Improves repository visibility and discoverability.
- Closes the loop: metadata is useful in both directions.

**Origin**: 
this tool started as [project 5](https://github.com/elixir-europe/biohackathon-projects-2025/blob/main/5.md) 
at the ELIXIR BioHackathon Europe 2025 
([original repository](https://github.com/bio-tools/biohackathon2025)).

---

## Features

| Direction          | What we do                                                             | Output                    |
|--------------------|------------------------------------------------------------------------|---------------------------|
| GitHub → bio.tools | Extract metadata from GitHub repositories                              | JSON bio.tools metadata   |
| bio.tools → GitHub | Propose improvements to GitHub repositories based on bio.tools records | PR                        |


## Installation

Requires Python 3.12+ and `git` on the `PATH`.

```bash
pip install metadata-bridge
bridge --help
```

Set `GITHUB_TOKEN` (and `HUGGINGFACE_TOKEN` for LLM-generated descriptions) in your environment or a `.env` file;
see [`.env.example`](https://github.com/bio-tools/metadata-bridge/blob/dev/.env.example).
A Docker image setup is described in the [Deployment guide](https://bio-tools.github.io/metadata-bridge/deployment_guide.html).

```bash
# GitHub -> bio.tools: print bio.tools metadata for a repo
bridge cli github-to-biotools extract OWNER REPO

# bio.tools -> GitHub: open a PR with improvements from a bio.tools entry
bridge cli biotools-to-github update BIOTOOLS_ID OWNER REPO
```

See the [User guide](https://bio-tools.github.io/metadata-bridge/user_guide.html) for details and the REST API.

## Development quick start

```bash
# clone
git clone https://github.com/bio-tools/metadata-bridge.git
cd metadata-bridge

# install (all groups)
poetry install

# enable quality hooks
poetry run pre-commit install --hook-type pre-commit --hook-type pre-push
```

Run the API (with auto-reload). Access Swagger at [localhost:8000/docs](http://localhost:8000/docs).

```bash
poetry run bridge api
```

Use the CLI:

```bash
poetry run bridge cli --help
```

## Documentation

The documentation is available at [https://bio-tools.github.io/metadata-bridge/](https://bio-tools.github.io/metadata-bridge/).

Preview on [localhost](http://localhost:8000):
```bash
poetry run poe gen-diagrams
poetry run poe gen-docs
python -m http.server --directory docs/build
```

## Contributing

Contributions are welcome! 
Please read the [CONTRIBUTING](https://github.com/bio-tools/metadata-bridge/blob/dev/CONTRIBUTING.md) for branching, PR rules, and code style.
Read the [Developer guide](https://bio-tools.github.io/metadata-bridge/dev_guide.html) for setup and commands.

## Citing

If you use this tool, please cite it using the metadata in [CITATION.cff](https://github.com/bio-tools/metadata-bridge/blob/dev/CITATION.cff)
(GitHub's "Cite this repository" button uses it too).

---
## License
This project is licensed under Apache 2.0. See the [LICENSE](https://github.com/bio-tools/metadata-bridge/blob/dev/LICENSE.txt) file for details.