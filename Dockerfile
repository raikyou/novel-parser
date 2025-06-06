FROM ghcr.io/astral-sh/uv:python3.9-alpine

WORKDIR /app

# Install dependencies
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --compile-bytecode --no-dev --no-cache

# Create volumes for novel files and data
VOLUME /app/docs /app/data

# Expose the API port
EXPOSE 5001

# Run the application
CMD ["uv", "run", "main.py"]
