FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock /app/
RUN pip install --no-cache-dir uv && \
    uv venv .venv && \
    .venv/bin/uv sync --frozen --no-dev --no-install-project

COPY . /app
RUN .venv/bin/uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH="/app/src"

RUN chmod +x /app/scripts/bootstrap.sh

CMD ["/app/scripts/bootstrap.sh", "run"]
