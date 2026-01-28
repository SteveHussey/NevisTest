FROM ghcr.io/astral-sh/uv:trixie-slim AS builder
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_INSTALLER_METADATA=1

## Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python
ENV UV_PYTHON_PREFERENCE=only-managed

## Install Python before the project for caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv python install 3.13

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable
COPY ./src /app/src
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Then, use a final image without uv
FROM docker.io/debian:trixie-slim as runtime

RUN groupadd -g 1000 nevis && useradd -m -u 1000 -g nevis nevis

# Copy the Python version
COPY --from=builder --chown=nevis:nevis /python /python

WORKDIR /env

# Copy the application from the builder
COPY --from=builder --chown=nevis:nevis /app/.venv /env
USER nevis

# Place executables in the environment at the front of the path
ENV PATH="/env/bin:$PATH"

# Run the FastAPI application by default
ENTRYPOINT ["python"]
CMD ["-m", "nevis"]
