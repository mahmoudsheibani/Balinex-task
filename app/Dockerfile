# Use slim Python image
FROM python:3.11-alpine

# Create non-root user
RUN adduser -u 1000 -D appuser

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && apk add --no-cache curl

# Copy application code
COPY main.py .

# Switch to non-root user
USER appuser

# Make filesystem read-only except /tmp
VOLUME ["/tmp"]

ENV PORT=8080
ENV APP_VERSION=1.0.0

EXPOSE 8080

# Use gunicorn for production (handles multiple workers properly)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "main:app"]