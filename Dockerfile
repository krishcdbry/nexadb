# NexaDB Dockerfile
# Build: docker build -t nexadb:latest .
# Run: docker run -p 6970:6970 -p 6969:6969 -p 9999:9999 nexadb:latest

FROM python:3.11-slim

# Metadata
LABEL maintainer="NexaDB Team <team@nexadb.dev>"
LABEL description="NexaDB - Database for AI Developers"
LABEL version="2.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY nexadb_server.py .
COPY nexadb_binary_server.py .
COPY admin_server.py .
COPY veloxdb_core.py .
COPY storage_engine.py .
COPY nexadb_client.py .
COPY reset_root_password.py .
COPY admin_panel/ admin_panel/

# Install Python dependencies
RUN pip install --no-cache-dir msgpack

# Download nexa CLI binary (architecture-aware)
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        NEXA_URL="https://github.com/krishcdbry/nexadb/releases/download/cli-v2.0.0/nexa-x86_64-unknown-linux-gnu"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        NEXA_URL="https://github.com/krishcdbry/nexadb/releases/download/cli-v2.0.0/nexa-aarch64-unknown-linux-gnu"; \
    fi && \
    curl -fsSL "$NEXA_URL" -o /usr/local/bin/nexa && \
    chmod +x /usr/local/bin/nexa

# Create data directory
RUN mkdir -p /data

# Expose ports
# 6970 - Binary Protocol (10x faster)
# 6969 - JSON REST API
# 9999 - Admin Web UI
EXPOSE 6970 6969 9999

# Set environment variables
ENV DATA_DIR=/data
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import socket; s=socket.socket(); s.connect(('localhost', 6970)); s.close()" || exit 1

# Run NexaDB (starts all services)
CMD ["python3", "nexadb_server.py", "--data-dir", "/data", "--host", "0.0.0.0"]
