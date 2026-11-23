# Installation

The bridge needs Python 3.12 or newer and `git` on the `PATH`
(it uses git to clone repositories and check wikis).

## From PyPI

```sh
pip install metadata-bridge
```

or, to keep it isolated from other tools:

```sh
pipx install metadata-bridge
```

Check it works:

```sh
bridge --version
bridge --help
```

## With Docker

See the [Deployment guide](deployment_guide.md#docker).

## From source

For development, clone the repository and install it with [Poetry](https://python-poetry.org/docs/#installation):

```sh
git clone https://github.com/bio-tools/metadata-bridge.git
cd metadata-bridge
poetry install
```

The [Developer guide](dev_guide.md) covers the rest of the development setup.
