# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
  gcc \
  python3-dev \
  curl \
  build-essential \
  pkg-config \
  cmake \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
  curl \
  sqlite3 \
  && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
  chown -R appuser:appuser /app

# Create and set permissions for vectordb directory
RUN mkdir -p /app/vectordb && \
  chown -R appuser:appuser /app/vectordb

# Copy application code
COPY --chown=appuser:appuser . .

# Create entrypoint script
RUN echo '#!/bin/bash\n\
  set -e\n\
  \n\
  # Check for required environment variables\n\
  if [ -z "$OPENAI_API_KEY" ]; then\n\
  echo "Error: OPENAI_API_KEY environment variable is required"\n\
  exit 1\n\
  fi\n\
  \n\
  # Set default values for optional environment variables\n\
  export HOST=${HOST:-0.0.0.0}\n\
  export PORT=${PORT:-8001}\n\
  export LOG_LEVEL=${LOG_LEVEL:-INFO}\n\
  export COLLECTION_NAME=${COLLECTION_NAME:-sitecheck}\n\
  export VECTORDB_PATH=${VECTORDB_PATH:-/app/vectordb}\n\
  \n\
  # Start the application\n\
  exec uvicorn agentforge.main:app --host "$HOST" --port "$PORT" --log-level "${LOG_LEVEL,,}"\n\
  ' > /app/entrypoint.sh && \
  chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8001/health || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"] 