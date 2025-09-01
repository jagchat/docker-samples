FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker.py .

# Environment defaults (can be overridden)
ENV RABBITMQ_HOST=rabbitmq
ENV QUEUE_NAME=my-queue
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash worker
USER worker

# Run the application
CMD ["python", "worker.py"]

# or run Python unbuffered
# CMD ["python","-u","worker.py"]
