FROM python:3.12-slim

# Copy the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cached unless pyproject.toml or uv.lock change)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application source and install the project
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# Put the virtual environment on the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Cloud Run injects $PORT (defaulting to 8080)
CMD ["sh", "-c", "uvicorn gcp_hello_world.main:app --host 0.0.0.0 --port ${PORT:-8080}"]