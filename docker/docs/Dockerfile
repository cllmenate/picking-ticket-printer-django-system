# ─── MkDocs Documentation Server ─────────────────────────────────────────────
# Lightweight image dedicated to serving project documentation.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency manifests and install deps only (skip project source install).
# --no-install-project avoids hatchling trying to build core/, apps/, ticket_printer/
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

# Copy documentation source and config
COPY docs/ ./docs/
COPY mkdocs.yml ./

# Non-root user
RUN addgroup --system docs && adduser --system --ingroup docs docs
USER docs

# Railway injects PORT; default to 8001 for local use
ENV PORT=8001

# Use shell form so $PORT is expanded at runtime
CMD /app/.venv/bin/mkdocs serve -a 0.0.0.0:${PORT}
