FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY . .

RUN poetry install

CMD ["poetry", "run", "python", "-m", "uvicorn", "bridge.adapters.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
