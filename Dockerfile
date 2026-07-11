# Use Python 3.13 slim image based on Debian Bookworm as the base image
FROM python:3.13-slim-bookworm

# Copy the UV binary from an external container to the /bin directory
COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/

# Create an unprivileged user and the application directory early so that
# dependency installation and source code ownership are correct from the start.
# Using a fixed UID/GID lets cache mounts be owned by the app user.
RUN groupadd -r app \
    && useradd -r -u 1000 -g app -d /home/app -m -s /bin/bash app \
    && mkdir -p /app \
    && chown app:app /app

# Set the working directory inside the container
WORKDIR /app

# Run subsequent build steps as the unprivileged user to avoid an expensive
# recursive chown at the end of the build.
USER app

# Use copy link mode to avoid cross-filesystem hardlink warnings when the uv
# cache mount and the project virtual environment are on different filesystems.
ENV UV_LINK_MODE=copy
ENV HOME=/home/app

# Install dependencies using a cache mount and bind mounts for the dependency
# definition files. Because only pyproject.toml and uv.lock are mounted here,
# this layer is cached independently of source code changes.
RUN --mount=type=cache,target=/home/app/.cache/uv,uid=1000,gid=1000 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project \
    && uv pip install "setuptools>=69" wheel

# Copy project source code with correct ownership. These files change frequently,
# so they are placed after the dependency layer to maximize cache reuse.
COPY --chown=app:app src/ ./src/
COPY --chown=app:app tools/ ./tools/
COPY --chown=app:app utils/ ./utils/
COPY --chown=app:app api/ ./api/
COPY --chown=app:app server.py .

# Copy the dependency definition files into the image so they are available
# for the final project sync and at runtime.
COPY --chown=app:app pyproject.toml uv.lock ./

# Synchronize the project code into the virtual environment.
# Use --no-build-isolation so uv can use the setuptools/wheel already installed
# in the virtual environment instead of fetching them at runtime.
RUN --mount=type=cache,target=/home/app/.cache/uv,uid=1000,gid=1000 \
    uv sync --locked --no-build-isolation

# Runtime configuration
ENV PORT=8000
EXPOSE 8000

# Set the default command to run the FastAPI app
CMD ["uv", "run", "server.py"]
