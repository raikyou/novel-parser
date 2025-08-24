FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

# Install dependencies
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --compile-bytecode --no-dev --no-cache

# Expose the API port
EXPOSE 5001

# Run the application
CMD ["uv", "run", "novel-parser"]
