# Bidirectional bridge: GitHub ⇄ bio.tools

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
| GitHub → bio.tools | Extract metadata from GitHub repositories                              | JSON bio.tools metatadata |
| bio.tools → GitHub | Propose improvements to GitHub repositories based on bio.tools records | PR                        |


## Quick start

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
Please read the [CONTRIBUTING](CONTRIBUTING.md) for branching, PR rules, and code style.
Read the [Developer guide](https://bio-tools.github.io/metadata-bridge/dev_guide.html) for setup and commands.

---
## License
This project is licensed under Apache 2.0. See the [LICENSE](LICENSE.txt) file for details.