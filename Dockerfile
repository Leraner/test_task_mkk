# --- builder: ставим зависимости в .venv через uv ---
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.10.8 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# --- runtime: только интерпретатор, готовое окружение и код ---
FROM python:3.14-slim

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --uid 1000 app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY src ./src

USER app

EXPOSE 8000

CMD ["python", "-m", "src.shared.web.main"]
