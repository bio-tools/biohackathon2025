# Bidirectional bridge: GitHub ⇄ bio.tools

**Goal**: 
make software metadata painless. 
This tool extracts high-quality metadata from GitHub repos 
to build bio.tools entries
and uses bio.tools records to propose improvements back to GitHub 
(badges, descriptions, files). 
During the BioHackathon it targets GitHub and bio.tools only, 
but the architecture is intentionally pluggable for more backends later.

**Why**:
- Reduces manual work in software metadata curation.
- Improves repository visibility and discoverability.
- Closes the loop: metadata is useful in both directions.

Full abstract: 
[Biohackathon 2025 project](https://github.com/elixir-europe/biohackathon-projects-2025/blob/main/5.md) 
---

## Features

| Direction          | What we do                                                             | Output                    |
|--------------------|------------------------------------------------------------------------|---------------------------|
| GitHub → bio.tools | Extract metadata from GitHub repositories                              | JSON bio.tools metatadata |
| bio.tools → GitHub | Propose improvements to GitHub repositories based on bio.tools records | PR                        |


## Quick start

```bash
# clone
git clone https://github.com/bio-tools/biohackathon2025.git
cd biohackathon2025

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

The documentation is available at [https://bio-tools.github.io/biohackathon2025/](https://bio-tools.github.io/biohackathon2025/).

Preview on [localhost](http://localhost:8000):
```bash
poetry run gen-diagrams
poetry run gen-docs
python -m http.server --directory docs/build
```

## Contributing

Contributions are welcome! 
Please read the [CONTRIBUTING](CONTRIBUTING.md) or branching, PR rules, and code style.
Read the [Developer guide](https://bio-tools.github.io/biohackathon2025/dev_guide.html) for setup and commands.

---
## License
This project is licensed under Apache 2.0. See the [LICENSE](LICENSE.txt) file for details.