import pika
import json
import time
import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify
import threading
import logging
import re
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

# Configure logging
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s - %(levelname)s - [{CONTAINER_ID}] - %(message)s')
logger = logging.getLogger(__name__)

class RabbitMQPublisher:
    def __init__(self):
        # Handle Kubernetes environment variables properly
        self.rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        
        # Parse port from potentially complex format
        rabbitmq_port_env = os.getenv('RABBITMQ_PORT', '5672')
        if rabbitmq_port_env.startswith('tcp://'):
            # Extract port from tcp://host:port format
            port_match = re.search(r':(\d+)$', rabbitmq_port_env)
            self.rabbitmq_port = int(port_match.group(1)) if port_match else 5672
        else:
            try:
                self.rabbitmq_port = int(rabbitmq_port_env)
            except ValueError:
                logger.warning(f"ERROR: Could not parse port from {rabbitmq_port_env}, using default 5672")
                self.rabbitmq_port = 5672
        
        self.rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'admin')
        self.rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'admin123')
        self.queue_name = os.getenv('QUEUE_NAME', 'work_queue')
        
        self.connection = None
        self.channel = None
        self.message_count = 0
        
        logger.info(f"Publisher initialized - Host: {self.rabbitmq_host}, Port: {self.rabbitmq_port}, Queue: {self.queue_name}")
        logger.info(f"Raw RABBITMQ_PORT env: {rabbitmq_port_env}")
        
    def connect(self):
        """Connect to RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                return True
                
            logger.info(f"Connecting to RabbitMQ at {self.rabbitmq_host}:{self.rabbitmq_port}")
            
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
            
            # Declare queue
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            logger.info("Successfully connected to RabbitMQ and declared queue")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
            return False
    
    def ensure_connection(self):
        """Ensure we have a working connection"""
        try:
            if self.connection is None or self.connection.is_closed:
                return self.connect()
            
            # Test the connection
            self.connection.process_data_events(time_limit=0)
            return True
            
        except Exception as e:
            logger.warning(f"ERROR: Connection test failed, reconnecting: {e}")
            return self.connect()
    
    def publish_message(self, message_data):
        """Publish a single message to RabbitMQ"""
        try:
            # Ensure we have a working connection
            if not self.ensure_connection():
                logger.error("Cannot establish connection to RabbitMQ")
                return False
            
            # Create the message
            enhanced_message = {
                'id': self.message_count,
                'data': message_data,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'publisher',
                'publisher_container_id': CONTAINER_ID
            }
            
            # Publish the message
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(enhanced_message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    content_type='application/json'
                )
            )
            
            self.message_count += 1
            logger.info(f"Successfully published message {self.message_count}: {message_data}")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error publishing message: {e}")
            # Reset connection on error
            try:
                if self.connection:
                    self.connection.close()
            except:
                pass
            self.connection = None
            self.channel = None
            return False
    
    def get_queue_status(self):
        """Get current queue statistics"""
        try:
            if not self.ensure_connection():
                logger.error("Cannot connect to get queue status")
                return None
            
            method = self.channel.queue_declare(queue=self.queue_name, durable=True, passive=True)
            return {
                'queue_name': self.queue_name,
                'message_count': method.method.message_count,
                'consumer_count': method.method.consumer_count
            }
        except Exception as e:
            logger.error(f"ERROR: Error getting queue status: {e}")
            return None
    
    def publish_batch(self, messages, delay_seconds=0.5):
        """Publish multiple messages"""
        successful = 0
        failed = 0
        
        for i, message in enumerate(messages):
            if self.publish_message(message):
                successful += 1
            else:
                failed += 1
            
            if delay_seconds > 0 and i < len(messages) - 1:
                time.sleep(delay_seconds)
        
        logger.info(f"Batch complete: {successful} successful, {failed} failed")
        return {'successful': successful, 'failed': failed}
    
    def test_connection(self):
        """Test the connection and return status"""
        try:
            if self.connect():
                status = self.get_queue_status()
                if status:
                    return True, f"Connection successful. Queue has {status['message_count']} messages."
                else:
                    return True, "Connection successful but couldn't get queue status."
            else:
                return False, "ERROR: Failed to connect to RabbitMQ"
        except Exception as e:
            return False, f"ERROR: Connection test failed: {e}"

# Flask app
app = Flask(__name__)
publisher = RabbitMQPublisher()

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'rabbitmq-publisher',
        'container_id': CONTAINER_ID,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/debug/env', methods=['GET'])
def debug_env():
    """Debug endpoint to see environment variables"""
    return jsonify({
        'container_id': CONTAINER_ID,
        'RABBITMQ_HOST': os.getenv('RABBITMQ_HOST'),
        'RABBITMQ_PORT': os.getenv('RABBITMQ_PORT'),
        'RABBITMQ_USERNAME': os.getenv('RABBITMQ_USERNAME'),
        'RABBITMQ_PASSWORD': os.getenv('RABBITMQ_PASSWORD')[:3] + '***' if os.getenv('RABBITMQ_PASSWORD') else None,
        'QUEUE_NAME': os.getenv('QUEUE_NAME'),
        'parsed_port': publisher.rabbitmq_port,
        'all_rabbitmq_vars': {k: v for k, v in os.environ.items() if 'RABBIT' in k.upper()}
    })

@app.route('/connection/test', methods=['GET'])
def test_connection():
    try:
        success, message = publisher.test_connection()
        return jsonify({
            'status': 'success' if success else 'error',
            'message': message,
            'container_id': CONTAINER_ID
        }), 200 if success else 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e), 'container_id': CONTAINER_ID}), 500

@app.route('/publish', methods=['POST'])
def publish_single_message():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        message = data.get('message', 'Default test message')
        logger.info(f"Received publish request: {message}")
        
        success = publisher.publish_message(message)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Message published successfully',
                'data': message,
                'container_id': CONTAINER_ID
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to publish message',
                'container_id': CONTAINER_ID
            }), 500
            
    except Exception as e:
        logger.error(f"ERROR: Error in publish endpoint: {e}")
        return jsonify({'error': str(e), 'container_id': CONTAINER_ID}), 500

@app.route('/publish/batch', methods=['POST'])
def publish_batch_messages():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        messages = data.get('messages', [])
        count = data.get('count', len(messages))
        delay = data.get('delay', 0.5)
        
        if not messages and count > 0:
            messages = [f"Test message {i+1}" for i in range(count)]
        
        if not messages:
            return jsonify({'error': 'No messages to publish'}), 400
        
        result = publisher.publish_batch(messages, delay)
        
        return jsonify({
            'status': 'completed',
            'result': result,
            'total_messages': len(messages),
            'container_id': CONTAINER_ID
        })
        
    except Exception as e:
        logger.error(f"ERROR: Error in batch publish: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/queue/status', methods=['GET'])
def get_queue_status():
    try:
        status = publisher.get_queue_status()
        if status:
            status['container_id'] = CONTAINER_ID
            return jsonify(status)
        else:
            return jsonify({'error': 'Unable to get queue status', 'container_id': CONTAINER_ID}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'container_id': CONTAINER_ID}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting publisher on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)