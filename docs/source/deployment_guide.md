# Deployment guide

This guide covers running the bridge API as a long-lived service.
For local development, see the [Developer guide](dev_guide.md) instead.

## Configuration

All settings come from environment variables (or a `.env` file in the working directory).
See `.env.example` in the repository for the full list. The most important ones:

| Variable            | Required for                                         |
|---------------------|------------------------------------------------------|
| `GITHUB_TOKEN`      | GitHub API calls, cloning repos, creating PRs/issues |
| `HUGGINGFACE_TOKEN` | LLM-generated descriptions (GitHub → bio.tools)      |
| `LOG_LEVEL`         | Optional, defaults to `INFO`                         |

The service endpoints (`GITHUB_API_URL`, `BIOTOOLS_API_URL`, ...) have sensible defaults and
only need to be set to point at a different instance.

## Docker

The repository ships a `Dockerfile` that installs the locked runtime dependencies and runs the API
on port 8000 as a non-root user.

Build the image from the repository root:

```bash
docker build -t metadata-bridge .
```

Run it, passing configuration through an env file:

```bash
docker run --rm -p 8000:8000 --env-file .env metadata-bridge
```

The Swagger UI is then available at [localhost:8000/docs](http://localhost:8000/docs).

The same image can run the CLI:

```bash
docker run --rm --env-file .env metadata-bridge bridge cli --help
```

## Without Docker

Install the package from PyPI. `git` must be available on the `PATH`,
since the bridge uses it to clone repositories and check wikis.

```bash
pip install metadata-bridge
bridge api --host 0.0.0.0 --port 8000 --no-reload
```

Always pass `--no-reload` outside development: hot reload is on by default for local work.

When running behind a reverse proxy, forward requests to the port above;
the API serves its OpenAPI schema at `/openapi.json` and docs at `/docs` and `/redoc`.
