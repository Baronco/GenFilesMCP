# Use Python 3.13 slim image based on Debian Bookworm as the base image
FROM python:3.13-slim-bookworm

# Copy the UV binary from an external container to the /bin directory
COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy the project configuration files
COPY pyproject.toml ./
COPY uv.lock ./

# Copy template directorie into the container
COPY src/ ./src/
COPY utils/ ./utils/
COPY tools/ ./tools/

# Install dependencies using UV, leveraging cache for faster builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy the main server script into the container
COPY server.py .

# Synchronize dependencies again to ensure everything is up-to-date
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Create an unprivileged user and ensure the application directory is owned by that user.
# Build steps above run as root (needed for package installation). At runtime we drop to
# the unprivileged `app` user to reduce risk from container compromise.
RUN groupadd -r app \
    && useradd -r -g app -d /home/app -m -s /bin/bash app \
    && chown -R app:app /app

# Set HOME and switch to the unprivileged user for runtime
ENV HOME=/home/app
ENV PORT=8000
USER app

# Expose the API port
EXPOSE 8000

# Set the default command to run the FastAPI app
CMD ["uv", "run", "server.py"]