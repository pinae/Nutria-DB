FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Install dependencies first so this layer is cached between code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY nutriaDB /app/nutriaDB
COPY docker-setup/init_and_run.sh /app/init_and_run.sh
RUN chmod +x /app/init_and_run.sh

WORKDIR /app/nutriaDB
EXPOSE 8000
CMD ["/app/init_and_run.sh"]
