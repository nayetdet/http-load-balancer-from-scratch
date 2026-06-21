# Build Stage
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder
ENV UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Runtime Stage
FROM python:3.14-slim-trixie
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app .

EXPOSE 3000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:3000", "main:app"]
