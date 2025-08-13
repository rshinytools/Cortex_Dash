FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Copy requirements
COPY requirements-prod.txt requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/studies

# Make startup script executable
RUN chmod +x /app/scripts/startup.sh

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run startup script which handles initialization and starts the app
ENTRYPOINT ["/bin/bash", "/app/scripts/startup.sh"]
