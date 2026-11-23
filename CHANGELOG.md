# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `bridge --version` and a version on the API's OpenAPI schema.
- Release workflow publishing to PyPI on `vX.Y.Z` tags, plus Dependabot.
- Dockerfile for running the API, a deployment guide, an installation page and a user guide.
- `bridge api --no-reload` to turn off hot reload.

### Changed
- Moved from `bio-tools/biohackathon2025` to `bio-tools/metadata-bridge`; the package is published as `metadata-bridge`.
- Dev helpers (`lint`, `fmt`, `gen-*`, ...) are now poe tasks: `poetry run poe <task>`.
- The "bridge" README badge links to the new docs site; old badges are replaced instead of duplicated.
- Docs are only deployed from the deploy branch (`DOCS_DEPLOY_BRANCH`, default `dev`); PRs just build them.
- `pydantic`, `pyyaml` and `packaging` are declared as dependencies; unused `requests` is dropped.

### Fixed
- Badge logos are bundled in the package, so they work when installed from PyPI.

## 0.1.0

Initial version developed during the ELIXIR BioHackathon Europe 2025 (project 5).
