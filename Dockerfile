# ─── Base stage ──────────────────────────────────────────────────────────────
FROM python:3.13-slim AS base

# Prevents Python from writing .pyc files and enables stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH"

# Install uv from the official image — available system-wide (/usr/local/bin)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install system dependencies required by psycopg2 and certificate signing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# ─── Dependencies stage ──────────────────────────────────────────────────────
FROM base AS deps

# Copy only dependency manifests first (leverages Docker layer cache)
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# ─── Runtime stage ───────────────────────────────────────────────────────────
FROM base AS runtime

# Copy installed virtual environment from deps stage
COPY --from=deps /app/.venv /app/.venv

# Copy application source
COPY . .

# Copy and set permissions on entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Non-root user for security
RUN addgroup --system django && adduser --system --ingroup django django
RUN chown -R django:django /app /entrypoint.sh
USER django

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

