# User guide

The bridge works in two directions:

- **GitHub → bio.tools**: extract bio.tools metadata (JSON) from a GitHub repository,
  optionally merged with an existing bio.tools entry.
- **bio.tools → GitHub**: propose improvements to a GitHub repository based on its bio.tools entry,
  as a pull request (README badges, description, citation, license, topics, ...) and optionally issues.

See [Installation](install.md) to get the `bridge` command, and set at least `GITHUB_TOKEN`
(environment variable or `.env` file, see `.env.example`).
Generating descriptions from READMEs with an LLM also needs `HUGGINGFACE_TOKEN`.

## Command line

### GitHub → bio.tools

```bash
bridge cli github-to-biotools extract OWNER REPO [--biotools-id ID]
```

Prints the extracted bio.tools metadata as JSON.
Pass `--biotools-id` when the tool already has a bio.tools entry, so the existing record is used as the base.

### bio.tools → GitHub

```bash
bridge cli biotools-to-github update BIOTOOLS_ID OWNER REPO [--allow-issues | --no-allow-issues]
```

Forks `OWNER/REPO` into the account that owns `GITHUB_TOKEN` (or reuses an existing fork),
commits the proposed changes on a new branch and opens a pull request against the original repository.
With `--allow-issues`, suggestions that can't be expressed as file changes are opened as issues.

## REST API

Start the API with `bridge api` (see the [Deployment guide](deployment_guide.md) for running it as a service).
The interactive docs are at `/docs`.

| Endpoint                   | Body                                                     | Does                         |
|----------------------------|----------------------------------------------------------|------------------------------|
| `POST /github-to-biotools` | `{"owner", "repo", "biotools_id"?}`                      | Returns bio.tools metadata   |
| `POST /biotools-to-github` | `{"biotools_id", "owner", "repo", "allow_issues"?}`      | Opens a PR (and issues)      |

Example:

```bash
curl -X POST http://localhost:8000/github-to-biotools \
  -H "Content-Type: application/json" \
  -d '{"owner": "bio-tools", "repo": "metadata-bridge"}'
```

## Python

The same operations are available from Python:

```python
from bridge import extract_meta_from_repo, create_pr_issues_from_meta
```

See the [API reference](api_reference/index_user) for their signatures.
