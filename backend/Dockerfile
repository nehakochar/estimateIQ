# ─────────────────────────────────────────────────────────────────
# Dockerfile — Backend Container Definition
# ─────────────────────────────────────────────────────────────────
# This file tells Docker how to build the backend container image.
# Docker reads it top-to-bottom and creates a layered image.
#
# Key concept — layer caching:
#   Docker caches each step. If requirements.txt hasn't changed,
#   it reuses the cached pip install layer instead of re-running it.
#   That's why we COPY requirements.txt BEFORE copying app code.
# ─────────────────────────────────────────────────────────────────

# Use the official Python 3.12 slim image as the base.
# 'slim' = smaller image size, no unnecessary OS packages.
FROM python:3.12-slim

# Set the working directory inside the container.
# All subsequent commands run from /app.
WORKDIR /app

# Copy requirements first — this layer is cached until requirements.txt changes.
COPY requirements.txt .

# Install all Python dependencies.
# --no-cache-dir keeps the image smaller (no pip cache stored).
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code into the container.
COPY app/ ./app/

# Tell Docker this container listens on port 8000.
# This is documentation only — actual port mapping is in docker-compose.yml.
EXPOSE 8000

# ─────────────────────────────────────────────────────────────────
# Start the FastAPI server with uvicorn.
#
# --host 0.0.0.0  → listen on all network interfaces (required inside Docker)
# --port 8000     → the port uvicorn binds to inside the container
# --reload        → auto-restart when code changes (great for development)
#                   In production, remove --reload for better performance.
# ─────────────────────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
