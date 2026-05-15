FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY . .

RUN poetry install

CMD ["poetry", "run", "python", "-m", "uvicorn", "bridge.adapters.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
