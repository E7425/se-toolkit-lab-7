# Bot Dockerfile using uv
# See https://docs.astral.sh/uv/guides/integration/docker/

ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/

# ---
# Stage 1: Build the application
# ---

FROM ${REGISTRY_PREFIX}astral/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app/bot

# Copy bot project files
COPY bot/pyproject.toml bot/uv.lock ./

# Sync dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy bot source code
COPY bot/ ./

# Sync the project (installs bot as editable package)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# ---
# Stage 2: Final runtime image
# ---

FROM ${REGISTRY_PREFIX}python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Create non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy application from builder
COPY --from=builder --chown=nonroot:nonroot /app/bot /app/bot

# Add uv environment to PATH
ENV PATH="/app/bot/.venv/bin:$PATH"

# Set working directory
WORKDIR /app/bot

# Run as non-root user
USER nonroot

# Health check - verify bot can start
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import config; print('OK')" || exit 1

# Run the bot
CMD ["python", "bot.py"]
