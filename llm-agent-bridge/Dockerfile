# Multi-stage build for LLM Agent Bridge
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install the package
RUN pip install -e .

# Compile Protocol Buffers at build time
RUN python -m llm_agent_bridge.tools.proto_compiler \
    --proto-dir ./protos \
    --output-dir ./src/llm_agent_bridge/generated \
    --force

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.local/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create app directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY --from=builder /app /app

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/generated

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default environment variables
ENV BRIDGE_SERVER__HOST=0.0.0.0
ENV BRIDGE_SERVER__PORT=8000
ENV BRIDGE_SERVER__LOG_LEVEL=info
ENV BRIDGE_PROTO__PROTO_DIR=/app/protos
ENV BRIDGE_PROTO__OUTPUT_DIR=/app/generated

# Run the application
CMD ["python", "-m", "uvicorn", "llm_agent_bridge.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"] 