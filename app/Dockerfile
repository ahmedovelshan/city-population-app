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

# Environment settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=5000

WORKDIR /app

# Copy dependencies and code from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app /app

# Add non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Expose Flask port
EXPOSE $PORT

# Start the Flask app
CMD ["python", "app.py"]
