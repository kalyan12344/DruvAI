FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# CRITICAL: Use PORT environment variable for Cloud Run
# Cloud Run sets PORT dynamically, must bind to 0.0.0.0:$PORT
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120 --preload server:app