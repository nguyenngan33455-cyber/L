FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install package in development mode
RUN pip install -e ".[dev]"

# Create directories for models and logs
RUN mkdir -p /app/models /app/logs /app/replays

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ZBGYM_HOME=/app

# Default command
CMD ["python", "-m", "zbgym.cli.main", "help"]
