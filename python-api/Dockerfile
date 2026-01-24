# Multi-stage build for smaller image size
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip for better dependency resolution
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install Python dependencies with timeout to prevent hanging
RUN pip install --no-cache-dir --user --timeout=1000 -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Copy Python dependencies from builder to appuser's home
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code and startup script
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./start.sh ./start.sh

# Make startup script executable
RUN chmod +x ./start.sh

# Switch to non-root user
USER appuser

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port (Railway uses PORT env var dynamically)
EXPOSE 8000

# Run application using startup script
CMD ["./start.sh"]
