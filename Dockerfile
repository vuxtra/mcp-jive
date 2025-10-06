# Multi-stage Dockerfile for MCP Jive
# Builds both the Python MCP server and Next.js frontend in a single container

# Stage 1: Build Next.js frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend (static export)
RUN npm run build || echo "Frontend build failed, continuing with backend only"

# Stage 2: Build Python server
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Final runtime image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY src/ ./src/
COPY bin/ ./bin/
COPY mcp-server.py ./
COPY setup.py ./
COPY README.md ./

# Copy built frontend (if it exists)
COPY --from=frontend-builder /app/frontend/.next/static ./frontend_dist/static 2>/dev/null || true
COPY --from=frontend-builder /app/frontend/out ./frontend_dist/out 2>/dev/null || true

# Create data directory for LanceDB
RUN mkdir -p /app/data/lancedb

# Expose ports
# 3454 - MCP Server (HTTP + WebSocket)
EXPOSE 3454

# Set environment variables
ENV MCP_JIVE_PORT=3454 \
    MCP_JIVE_HOST=0.0.0.0 \
    LANCEDB_DATA_PATH=/app/data/lancedb \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3454/health || exit 1

# Run the server
CMD ["python", "mcp-server.py", "combined", "--host", "0.0.0.0", "--port", "3454"]
