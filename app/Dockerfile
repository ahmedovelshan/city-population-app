# -----------------------------
# Stage 1: Build stage
# -----------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# -----------------------------
# Stage 2: Final runtime stage
# -----------------------------
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PATH=/root/.local/bin:$PATH \
    PORT=5000

WORKDIR /app

# Copy only installed dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Copy app code
COPY --from=builder /app /app

# Add non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Expose port
EXPOSE $PORT

# Start the Flask app
CMD ["python", "app.py"]