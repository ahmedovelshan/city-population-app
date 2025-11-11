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
# Install dependencies globally in builder
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# -----------------------------
# Stage 2: Runtime stage
# -----------------------------
FROM python:3.11-slim

# Add non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

WORKDIR /app

# Environment settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PATH=/home/appuser/.local/bin:$PATH \
    PYTHONPATH=/app/.local/lib/python3.11/site-packages:$PYTHONPATH \
    PORT=5000

# Copy dependencies from builder
COPY --from=builder /install /home/appuser/.local
# Copy app code
COPY --from=builder /app /app

# Expose Flask port
EXPOSE $PORT

# Start the Flask app
CMD ["python", "app.py"]