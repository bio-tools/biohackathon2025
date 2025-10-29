# Developer guide

This guide explains how to set up a local development environment for bridge, 
run the CLI/API, and maintain code quality using the existing tooling.


## Prepare your environment

You need Python 3.12 (or higher) and Poetry.
If you don't have Poetry installed, you can install it by following the [instructions](https://python-poetry.org/docs/#installation)
or by running the following command:

```sh
pipx install poetry
```

Clone the repository and enter the project directory:

```sh
git clone https://github.com/bio-tools/biohackathon2025.git
cd biohackathon2025
```

## Install dependencies

Create and activate the virtual environment:

```sh
poetry install
```

Or install only specific groups:

```bash
poetry install --with dev  # install development dependencies
poetry install --with docs  # install documentation dependencies
```

## Enable pre-commit hooks

Pre-commit is installed automatically with the development dependencies.
To activate hooks in your local clone:

```bash
poetry install --with dev
poetry run pre-commit install --hook-type pre-commit --hook-type pre-push
```

What happens automatically:

| hook | stage      | description                                                              |
|------|------------|--------------------------------------------------------------------------|
| fmt  | pre-commit | Automatically fixes imports, formatting, and lint issues (Ruff + Black)  |
| lint | pre-push   | Checks that the codebase is clean and properly formatted before pushing. |

You can also run the same checks manually (very much encouraged):

```bash
poetry run [hook]
```

## Run locally

Before running the API or CLI, make sure to set up the required environment variables.
You can create a `.env` file in the project root based on the `.env.example` file.

### API

To run the API server with auto-reload:

```sh
poetry run bridge api
```
You can access the Swagger UI at [localhost:8000/docs](http://localhost:8000/docs).

### CLI

To see available commands:

```sh
poetry run bridge cli --help
```

### Helper scripts

Various helper scripts are available under the `scripts/` directory.

| script                | description                                             |
|-----------------------|---------------------------------------------------------|
| `gen-biotools-models` | Generate Pydantic models from the bio.tools JSON Schema |

You can run them using Poetry:

```bash
poetry run [script]
```

## Documentation

There are two scripts relevant to documentation generation:

| script                | description                                              |
|-----------------------|----------------------------------------------------------|
| `gen-diagrams`        | Generate architecture diagrams used by the documentation |
| `gen-docs`            | Generate Sphinx documentation                            |

You can run them using Poetry:

```bash
poetry run [script]
```

The `gen-diagrams` script requires [D2](https://d2lang.com/) to be installed. 
You can install it by following their [instructions](https://github.com/terrastruct/d2/blob/master/docs/INSTALL.md).

To view the documentation locally, run:

```bash
open docs/build/index.html  # on macOS
python -m http.server --directory docs/build  # any OS
```

If you run the latter command, you can access the documentation at [localhost:8000](http://localhost:8000).


## Dependencies

We use Poetry to manage dependencies.

Add runtime dependencies with:

```bash
poetry add [package]
```

Add development dependencies with:

```bash
poetry add --group dev [package]
```

Add documentation dependencies with:

```bash
poetry add --group docs [package]
```

## Contributing guidelines

Please refer to the [CONTRIBUTING.md](https://github.com/bio-tools/biohackathon2025/blob/dev/CONTRIBUTING.md) file for guidelines on contributing to this project.
