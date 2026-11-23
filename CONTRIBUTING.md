# Contributing guidelines

See the [Developer guide](https://bio-tools.github.io/metadata-bridge/dev_guide.html) in docs for details on setup, running API/CLI, docs preview, and local tooling.

## Ground rules

- Python ≥ 3.12 
- Package manager: [Poetry](https://python-poetry.org/docs/#installation)
- Style/Lint: Ruff + Black (configured in `pyproject.toml`)
- One clear purpose per PR: small, reviewable diffs
- No secrets in code: use env vars / `.env` locally; CI secrets are restricted
- Never edit auto-generated files by hand

## Branching & PRs

We keep two permanent branches and short-lived topic branches.

### Branch roles

| Branch | Purpose        | Rules                                                                                |
|--------|----------------|--------------------------------------------------------------------------------------|
| `main` | Release branch | Only merge from `dev` or `hotfix/*` (emergency). Tag release                         |
| `dev`  | Development    | All feature/bug PRs target dev. Keep green (working, buildable, test-passing state). |

### Topic branches

| Branch name       | Purpose     | Branch from | Merge into                                | Notes                                                                |
|-------------------|-------------|-------------|-------------------------------------------|----------------------------------------------------------------------|
| `feat/<slug>`     | Feature     | `dev`       | `dev`                                     | New features, enhancements                                           |
| `fix/<slug>`      | Bugfix      | `dev`       | `dev`                                     | Bug fixes, small changes                                             |
| `docs/<slug>`     | Docs        | `dev`       | `dev`                                     | Docs only updates                                                    |
| `chore/<slug>`    | Chore/Infra | `dev`       | `dev`                                     | Repo plumbing: tooling, CI/CD, dependencies, packaging, repo hygiene |
| `refactor/<slug>` | Refactor    | `dev`       | `dev`                                     | Code structure changes, no behavior changes                          |
| `test/<slug>`     | Tests       | `dev`       | `dev`                                     | Adding or updating tests                                             |
| `hotfix/<slug>`   | Hotfix      | `main`      | `main` and then back-merge `main` → `dev` | Emergency fixes                                                      |
| `exp/<slug>`      | Experiment  | `dev`       | `dev` or close                            | Prototypes, may be discarded                                         |

### Release flow

1. When `dev` is stable and ready for release, create a PR from `dev` to `main`.
2. After review and approval, merge (squash or merge commit) the PR and tag `vX.Y.Z`.
3. Back-merge `main` into `dev` to keep it up to date.

### Rebasing & merges

- Rebase topic branches on `dev` before opening/refreshing PRs.
- Use "Squash and merge" or "Merge commit" for PRs.

### PR checklist

- [ ] Rebased on latest `dev`
- [ ] Passes all pre-commit hooks (`poetry run poe fmt` and `poetry run poe lint`)
- [ ] Docs updated if needed
- [ ] Tests added/updated if needed
- [ ] Linked to an issue if applicable: Closes #ISSUE_NUMBER

## Code style

| Topic      | Standard                                        |
|------------|-------------------------------------------------|
| Lint       | Ruff ([tool.ruff])                              |
| Format     | Black (line length 120)                         |
| Imports    | Ruff isort (first party = `bridge`)             |
| Docstrings | Required top-level docstring per package/module |
| Style      | NumPy                                           |
| Types      | Prefer precise hints                            |


## Generated code

| File                                                                   | Purpose                                        | How to regenerate                |
|------------------------------------------------------------------------|------------------------------------------------|----------------------------------|
| `bridge/core/biotools.py`                                              | Pydantic models from bio.tools JSON            | `poetry run poe gen-biotools-models` |
| `bridge/core/github_repo.py` and `bridge/core/github_latest_release.py`| Pydantic models from github response JSONs ([repo](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository) & [latest release](https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#get-the-latest-release)) | `poetry run poe gen-github-models` |

- Never edit generated files directly.
- If schema or generator changes: regenerate and commit.


## CI behavior

### Build & Deploy Docs (`docs.yml`):

On push/PR to `dev` and push to `main`, 
CI installs deps, generates architecture diagrams (gen-diagrams), and builds Sphinx (gen-docs). 
Only pushes to `main` deploy to GitHub Pages. 
Preview links are attached to PRs and `dev` pushes. 
Do not commit built docs or diagrams.

| Event             | Branch | Build                                                                                                         | Deploy to Pages |
|-------------------|--------|---------------------------------------------------------------------------------------------------------------|-----------------|
| push              | `dev`  | Install deps (--with docs) + install D2 → `poetry run poe gen-diagrams` → `poetry run poe gen-docs` → upload artifact | No              |
| PR                | `dev`  | Same                                                                                                          | No              |
| push              | `main` | Same                                                                                                          | Yes             |
| workflow_dispatch | any    | Same                                                                                                          | Only if main    |


### Lint & unit tests (`tests.yml`):

Runs on every PR and on pushes to `dev` and `main`: `poetry run poe lint`, then `pytest` with coverage.

### Release (`release.yml`):

Runs when a `vX.Y.Z` tag is pushed. It checks the tag matches the version in `pyproject.toml`,
builds the sdist and wheel, publishes them to PyPI (trusted publishing, `pypi` environment),
and creates a GitHub release with generated notes.

To release: bump the version with `poetry version <patch|minor|major>`, update `CHANGELOG.md`,
merge `dev` → `main`, then tag `main` with `vX.Y.Z` and push the tag.

### Dependabot

Weekly grouped update PRs for Python dependencies and GitHub Actions, targeting `dev`.


## Design boundaries

| Layer       | Responsibility                                           | Examples                                                    |
|-------------|----------------------------------------------------------|-------------------------------------------------------------|
| `core`      | Pydantic domain models                                   | Data models for repos, schemas                              |
| `services`  | All interactions with external systems (APIs, git, LLMs) | API clients, ingestors, git wrappers, LLM interfaces        |
| `builders`  | Composition of models in `core` (using `services`)       | Transformers for building models from raw data              |
| `pipelines` | End-to-end flows for goals                              | Extracting metadata from a repo, suggesting file changes    |
| `adapters`  | CLI (typer) and API (fastapi) surfaces                   | Routers, commands, request models                           |
| `bootstrap` | Wiring and dependency injection                          | Registering composers for models, wiring goals to pipelines |
| `handlers`  | Orchestrators for (API/CLI) entrypoints for each goal    | Creating PRs, extracting metadata                           |


## Commit messages

Use clear, action-oriented subjects. Conventional commits encouraged.

| Good                                                  | Bad           |
|-------------------------------------------------------|---------------|
| `fix: handle 422 from GitHub PR API`                  | `fix stuff`   |
| `feat: add CLI command to extract metadata from repo` | `add code`    |
| `docs: update contributing guidelines`                | `update docs` |





