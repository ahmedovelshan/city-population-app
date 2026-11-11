FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY --chown=1000:1000 app.py .

USER 1000:1000

EXPOSE 5000

# Initialize Elasticsearch once, then run a production WSGI server.
CMD ["sh", "-c", "python -c 'import app; app.initialize()' && exec gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 30 --access-logfile - --error-logfile - app:app"]
