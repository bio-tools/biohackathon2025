FROM python:3.12-slim

# git is needed at runtime: the bridge clones repos and checks wikis with it
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install runtime deps from the lock file first, so this layer is cached
# unless dependencies change
RUN pip install --no-cache-dir "poetry>=2,<3" && \
    poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock README.md LICENSE.txt ./
RUN poetry install --only main --no-root --no-interaction --no-ansi

# then install the package itself
COPY src ./src
RUN poetry install --only-root --no-interaction --no-ansi

RUN useradd --create-home bridge
USER bridge

EXPOSE 8000

# configure via environment variables (see .env.example), e.g. `docker run --env-file .env ...`
CMD ["bridge", "api", "--host", "0.0.0.0", "--port", "8000", "--no-reload"]
