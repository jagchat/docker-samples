import pika
import json
import time
import os
import sys
import signal
import threading
from datetime import datetime
from flask import Flask, jsonify
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self):
        # Handle Kubernetes environment variables properly
        self.rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        
        # Parse port from potentially complex format
        rabbitmq_port_env = os.getenv('RABBITMQ_PORT', '5672')
        if rabbitmq_port_env.startswith('tcp://'):
            port_match = re.search(r':(\d+)$', rabbitmq_port_env)
            self.rabbitmq_port = int(port_match.group(1)) if port_match else 5672
        else:
            try:
                self.rabbitmq_port = int(rabbitmq_port_env)
            except ValueError:
                logger.warning(f"Could not parse port from {rabbitmq_port_env}, using default 5672")
                self.rabbitmq_port = 5672
        
        self.rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'admin')
        self.rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'admin123')
        self.queue_name = os.getenv('QUEUE_NAME', 'work_queue')
        self.consumer_id = os.getenv('HOSTNAME', f'consumer-{int(time.time())}')
        
        # Processing configuration
        self.min_processing_time = float(os.getenv('MIN_PROCESSING_TIME', '3.0'))
        self.max_processing_time = float(os.getenv('MAX_PROCESSING_TIME', '7.0'))
        
        # Connection objects
        self.connection = None
        self.channel = None
        self.consuming = False
        
        # Statistics
        self.messages_processed = 0
        self.messages_failed = 0
        self.start_time = datetime.utcnow()
        self.last_message_time = None
        
        # Graceful shutdown
        self.shutdown_requested = False
        
        logger.info(f"Consumer {self.consumer_id} initialized")
        logger.info(f"RabbitMQ: {self.rabbitmq_host}:{self.rabbitmq_port}, Queue: {self.queue_name}")
        logger.info(f"Processing time range: {self.min_processing_time}s - {self.max_processing_time}s")
        
    def connect(self):
        """Connect to RabbitMQ with retry logic"""
        max_retries = 10
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[{self.consumer_id}] Attempting to connect to RabbitMQ (attempt {attempt + 1}/{max_retries})")
                
                credentials = pika.PlainCredentials(self.rabbitmq_username, self.rabbitmq_password)
                parameters = pika.ConnectionParameters(
                    host=self.rabbitmq_host,
                    port=self.rabbitmq_port,
                    credentials=credentials,
                    connection_attempts=3,
                    retry_delay=2,
                    socket_timeout=10,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
                
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declare queue (idempotent)
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                
                # ✅ CRITICAL: Set QoS to process one message at a time per consumer
                # This ensures RabbitMQ distributes messages fairly across all consumers
                self.channel.basic_qos(prefetch_count=1)
                
                logger.info(f"[{self.consumer_id}] Successfully connected to RabbitMQ, consuming from queue: {self.queue_name}")
                return True
                
            except Exception as e:
                logger.error(f"[{self.consumer_id}] Failed to connect to RabbitMQ (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"[{self.consumer_id}] Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"[{self.consumer_id}] Max retries reached. Unable to connect to RabbitMQ")
                    return False
    
    def process_message(self, message_data):
        """Simulate message processing work"""
        try:
            # Extract message info
            message_id = message_data.get('id', 'unknown')
            data = message_data.get('data', 'no data')
            timestamp = message_data.get('timestamp', 'no timestamp')
            
            logger.info(f"[{self.consumer_id}] 🔄 STARTED processing message {message_id}: {data}")
            
            # Simulate variable processing time (real work would go here)
            import random
            processing_time = random.uniform(self.min_processing_time, self.max_processing_time)
            
            logger.info(f"[{self.consumer_id}] ⏳ Processing message {message_id} for {processing_time:.2f}s")
            
            # Simulate the actual work with progress indication
            steps = 4
            step_time = processing_time / steps
            
            for step in range(1, steps + 1):
                time.sleep(step_time)
                logger.info(f"[{self.consumer_id}] 📈 Message {message_id} - Step {step}/{steps} complete")
            
            # Simulate occasional failures (3% failure rate - reduced for better demo)
            if random.random() < 0.03:
                raise Exception("Simulated processing failure")
            
            logger.info(f"[{self.consumer_id}] ✅ COMPLETED processing message {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"[{self.consumer_id}] ❌ ERROR processing message: {e}")
            return False
    
    def message_callback(self, ch, method, properties, body):
        """Callback function for processing received messages"""
        message_start_time = time.time()
        
        try:
            # Parse the message
            message_data = json.loads(body.decode('utf-8'))
            message_id = message_data.get('id', 'unknown')
            
            logger.info(f"[{self.consumer_id}] 📥 RECEIVED message {message_id} from queue")
            
            # Process the message
            success = self.process_message(message_data)
            
            processing_duration = time.time() - message_start_time
            
            if success:
                # Acknowledge the message only after successful processing
                ch.basic_ack(delivery_tag=method.delivery_tag)
                self.messages_processed += 1
                self.last_message_time = datetime.utcnow()
                logger.info(f"[{self.consumer_id}] ✅ Message {message_id} ACKNOWLEDGED (took {processing_duration:.2f}s)")
            else:
                # Reject and requeue the message for retry
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                self.messages_failed += 1
                logger.warning(f"[{self.consumer_id}] 🔄 Message {message_id} REJECTED and REQUEUED")
                
        except json.JSONDecodeError as e:
            logger.error(f"[{self.consumer_id}] Invalid JSON in message: {e}")
            # Reject invalid messages without requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            self.messages_failed += 1
            
        except Exception as e:
            logger.error(f"[{self.consumer_id}] Unexpected error processing message: {e}")
            # Reject and requeue for retry
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            self.messages_failed += 1
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        try:
            if not self.connect():
                logger.error(f"[{self.consumer_id}] Failed to connect to RabbitMQ, cannot start consuming")
                return False
            
            # Set up consumer with proper callback
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.message_callback
            )
            
            self.consuming = True
            logger.info(f"[{self.consumer_id}] 🚀 STARTED consuming messages. Waiting for messages...")
            
            # ✅ FIXED: Use proper blocking start_consuming() instead of polling loop
            # This allows RabbitMQ to properly distribute messages across consumers
            try:
                self.channel.start_consuming()
            except KeyboardInterrupt:
                logger.info(f"[{self.consumer_id}] Keyboard interrupt received, stopping consumer...")
                self.channel.stop_consuming()
            
            logger.info(f"[{self.consumer_id}] 🛑 STOPPED consuming messages")
            return True
            
        except Exception as e:
            logger.error(f"[{self.consumer_id}] Error in consumer loop: {e}")
            return False
        finally:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming messages and close connections"""
        try:
            self.consuming = False
            if self.channel:
                try:
                    self.channel.stop_consuming()
                except:
                    pass
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info(f"[{self.consumer_id}] Consumer stopped gracefully")
        except Exception as e:
            logger.error(f"[{self.consumer_id}] Error stopping consumer: {e}")
    
    def get_stats(self):
        """Get consumer statistics"""
        uptime = datetime.utcnow() - self.start_time
        return {
            'consumer_id': self.consumer_id,
            'messages_processed': self.messages_processed,
            'messages_failed': self.messages_failed,
            'uptime_seconds': int(uptime.total_seconds()),
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'consuming': self.consuming,
            'connected': self.connection and not self.connection.is_closed,
            'rabbitmq_host': self.rabbitmq_host,
            'rabbitmq_port': self.rabbitmq_port,
            'queue_name': self.queue_name
        }
    
    def test_connection(self):
        """Test the connection and return status"""
        try:
            if self.connect():
                return True, "Connection successful"
            else:
                return False, "Failed to connect to RabbitMQ"
        except Exception as e:
            return False, f"Connection test failed: {e}"
    
    def request_shutdown(self):
        """Request graceful shutdown"""
        logger.info(f"[{self.consumer_id}] Graceful shutdown requested")
        self.shutdown_requested = True
        if self.channel:
            self.channel.stop_consuming()

# Flask app for health checks and monitoring
app = Flask(__name__)
consumer = RabbitMQConsumer()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'rabbitmq-consumer',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check"""
    stats = consumer.get_stats()
    if stats['connected']:
        return jsonify({
            'status': 'ready',
            'stats': stats
        }), 200
    else:
        return jsonify({
            'status': 'not_ready',
            'stats': stats
        }), 503

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get consumer statistics"""
    return jsonify(consumer.get_stats())

@app.route('/connection/test', methods=['GET'])
def test_connection():
    try:
        success, message = consumer.test_connection()
        return jsonify({
            'status': 'success' if success else 'error',
            'message': message
        }), 200 if success else 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/debug/env', methods=['GET'])
def debug_env():
    """Debug endpoint to see environment variables"""
    return jsonify({
        'RABBITMQ_HOST': os.getenv('RABBITMQ_HOST'),
        'RABBITMQ_PORT': os.getenv('RABBITMQ_PORT'),
        'RABBITMQ_USERNAME': os.getenv('RABBITMQ_USERNAME'),
        'RABBITMQ_PASSWORD': os.getenv('RABBITMQ_PASSWORD')[:3] + '***' if os.getenv('RABBITMQ_PASSWORD') else None,
        'QUEUE_NAME': os.getenv('QUEUE_NAME'),
        'parsed_port': consumer.rabbitmq_port,
        'consumer_id': consumer.consumer_id
    })

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Trigger graceful shutdown"""
    consumer.request_shutdown()
    return jsonify({'status': 'shutdown_requested'})

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, requesting graceful shutdown")
    consumer.request_shutdown()

def run_consumer():
    """Run the consumer in a separate thread"""
    logger.info("Starting consumer thread...")
    consumer.start_consuming()

def main():
    """Main function"""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start consumer in a separate thread
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    
    # Start Flask app for health checks
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting health check server on port {port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        consumer.request_shutdown()
        consumer_thread.join(timeout=10)

if __name__ == '__main__':
    main()