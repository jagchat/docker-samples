import pika
import time
import signal
import sys
import logging
import socket

def get_container_id():
    """Get the container ID from various sources"""
    try:
        # Method 1: Read from cgroup (most reliable)
        with open('/proc/self/cgroup', 'r') as f:
            for line in f:
                if 'docker' in line:
                    container_id = line.strip().split('/')[-1]
                    if len(container_id) == 64:  # Full Docker ID
                        return container_id[:12]  # Return short ID
        
        # Method 2: Hostname (Docker sets this to container ID by default)
        hostname = socket.gethostname()
        if len(hostname) == 12:  # Short container ID
            return hostname
            
        # Method 3: Check if hostname looks like container ID
        if len(hostname) > 8 and hostname.replace('-', '').replace('_', '').isalnum():
            return hostname[:12]
            
    except Exception as e:
        pass
    
    # Fallback: Use hostname or unknown
    return socket.gethostname()[:12] or "unknown"

CONTAINER_ID = get_container_id()
WORKER_NAME = f"worker-{CONTAINER_ID}"

# Configure logging
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s - %(levelname)s - [{CONTAINER_ID}] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

logger = logging.getLogger(__name__)

RABBITMQ_HOST = "rabbitmq"   # service name from docker-compose
QUEUE_NAME = "my-queue"

print(f"[{CONTAINER_ID}] Worker starting up...", flush=True)
logger.info(f"Worker {WORKER_NAME} initializing - Host: {RABBITMQ_HOST}, Queue: {QUEUE_NAME}")

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    logger.info(f"Connected to RabbitMQ successfully")
    print(f" [*] [{CONTAINER_ID}] Worker started. Waiting for messages...", flush=True)
    
except Exception as e:
    logger.error(f"ERROR: Failed to connect to RabbitMQ: {e}")
    sys.exit(1)

# Graceful shutdown flag
running = True

def shutdown_handler(sig, frame):
    global running
    logger.info(f" [x] Received SIGTERM, shutting down gracefully...")
    running = False
    if channel:
        channel.stop_consuming()

# Attach signal handler
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

def callback(ch, method, properties, body):
    start_time = time.time()
    try:
        message = body.decode()
        logger.info(f" [>] Processing message: {message}")
        time.sleep(5)  # simulate work
        ch.basic_ack(delivery_tag=method.delivery_tag)
        processing_time = time.time() - start_time
        logger.info(f"Completed processing in {processing_time:.2f}s")
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Reject and requeue message on error
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

try:
    while running:
        channel.start_consuming()
except Exception as e:
    logger.error(f"ERROR: Worker error: {e}")
finally:
    logger.info("Cleaning up connection...")
    if connection and not connection.is_closed:
        try:
            connection.close()
            logger.info("Connection closed cleanly")
        except Exception as e:
            logger.warning(f"ERROR closing connection: {e}")
    
    logger.info(f"Worker exited cleanly after processing message")
    print(f"Worker stopped. Processed message", flush=True)

    sys.exit(0)