# Use a slim Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy application code
COPY src ./src
# Copy config directory (will be overwritten by bind‐mount at runtime)
COPY config ./config

# Install runtime dependencies
RUN pip install --no-cache-dir requests pyyaml

# Default command
CMD ["python", "src/check.py"]