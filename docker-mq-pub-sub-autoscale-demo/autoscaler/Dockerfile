# Use Python slim base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    docker-cli \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy autoscaler script
COPY autoscale.py .

# Set environment defaults (can be overridden at runtime)
ENV RABBITMQ_API=http://rabbitmq:15672/api/queues/%2f/my-queue \
    RABBITMQ_USER=guest \
    RABBITMQ_PASS=guest \
    WORKER_PREFIX=rabbitmq-worker \
    WORKER_IMAGE=my-worker:latest \
    MIN_CONTAINERS=1 \
    MAX_CONTAINERS=10 \
    SCALE_UP_THRESHOLD=100 \
    SCALE_DOWN_THRESHOLD=10 \
    POLL_INTERVAL=10 \
    COOLDOWN_PERIOD=30 \
    MESSAGES_PER_WORKER=200 \
    STOP_TIMEOUT=60

# Run the autoscaler
CMD ["python", "autoscale.py"]
