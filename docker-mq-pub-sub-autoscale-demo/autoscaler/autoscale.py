import os
import time
import requests
import subprocess
import logging
import sys
import math
import pika
import signal
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ========================
# CONFIGURATION
# ========================
RABBITMQ_API = os.getenv("RABBITMQ_API", "http://localhost:15672/api/queues/%2f/my-queue")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
CONTAINER_NAME_PREFIX = os.getenv("WORKER_PREFIX", "worker")
IMAGE = os.getenv("WORKER_IMAGE", "my-worker:latest")

MIN_CONTAINERS = int(os.getenv("MIN_CONTAINERS", "1"))
MAX_CONTAINERS = int(os.getenv("MAX_CONTAINERS", "10"))
SCALE_UP_THRESHOLD = int(os.getenv("SCALE_UP_THRESHOLD", "100"))
SCALE_DOWN_THRESHOLD = int(os.getenv("SCALE_DOWN_THRESHOLD", "10"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
COOLDOWN_PERIOD = int(os.getenv("COOLDOWN_PERIOD", "30"))  # seconds
MESSAGES_PER_WORKER = int(os.getenv("MESSAGES_PER_WORKER", "200"))
SAFE_MPW = max(1, MESSAGES_PER_WORKER)
STOP_TIMEOUT = int(os.getenv("STOP_TIMEOUT", "60"))  # seconds to wait before force kill
COMPOSE_PROJECT = os.getenv("COMPOSE_PROJECT", "myapp")  # or derive from your compose `name:`
WORKER_COMPOSE_SERVICE = os.getenv("WORKER_COMPOSE_SERVICE", "worker")
DOCKER_NETWORK = os.getenv("DOCKER_NETWORK", "")

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

# Get container information
CONTAINER_ID = get_container_id()

# ========================
# LOGGING SETUP
# ========================
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s - %(levelname)s - [{CONTAINER_ID}] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("autoscaler")

logger.info(f"Autoscaler starting with container ID: {CONTAINER_ID}")
logger.info(f"Configuration: MIN={MIN_CONTAINERS}, MAX={MAX_CONTAINERS}, Scale Up>={SCALE_UP_THRESHOLD}, Scale Down<={SCALE_DOWN_THRESHOLD}")

# ========================
# HTTP SESSION WITH RETRIES
# ========================
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"]
)
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))

# ========================
# FUNCTIONS
# ========================
def ensure_queue_exists():
    try:
        params = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            credentials=pika.PlainCredentials(
                os.getenv("RABBITMQ_USER", "guest"),
                os.getenv("RABBITMQ_PASS", "guest")
            )
        )
        conn = pika.BlockingConnection(params)
        channel = conn.channel()
        queue_name = os.getenv("QUEUE_NAME", "my-queue")
        channel.queue_declare(queue=queue_name, durable=True)
        conn.close()
        logger.info(f"Ensured queue '{queue_name}' exists at startup")
    except Exception as e:
        logger.error(f"ERROR: Failed to ensure queue exists: {e}")

def get_queue_length():
    try:
        resp = session.get(RABBITMQ_API, auth=(RABBITMQ_USER, RABBITMQ_PASS), timeout=5)
        resp.raise_for_status()
        return resp.json().get("messages", 0)
    except Exception as e:
        logger.error(f"ERROR: Failed to fetch queue length: {e}")
        return 0

def get_running_workers():
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={CONTAINER_NAME_PREFIX}", "--format", "{{.ID}}"],
            stdout=subprocess.PIPE, text=True, check=True
        )
        workers = result.stdout.strip().splitlines()
        return workers if workers else []
    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR: Failed to list running containers: {e}")
        return []

def scale_workers(desired_count):
    current_workers = get_running_workers()
    current_count = len(current_workers)
    changed = False

    if desired_count > current_count:
        scale_up = desired_count - current_count
        logger.info(f"Scaling UP: Adding {scale_up} workers")
        for i in range(scale_up):
            name = f"{CONTAINER_NAME_PREFIX}-{int(time.time())}-{i}"
            try:
                run_cmd = ["docker", "run", "-d", "--name", name]
                # # 1. Start container with primary network (appnet)
                # run_cmd += ["--network", "myapp_appnet"]
                if DOCKER_NETWORK:
                    run_cmd += ["--network", DOCKER_NETWORK]
                # Compose labels so `down --remove-orphans` cleans them
                run_cmd += ["--label", f"com.docker.compose.project={COMPOSE_PROJECT}",
                            "--label", f"com.docker.compose.service={WORKER_COMPOSE_SERVICE}",
                            "--label", "autoscaler.owner=true"]  # our own ownership label for plan B

                # pass RabbitMQ envs to worker (optional but recommended)
                essential_env_vars = {
                    "PYTHONUNBUFFERED": "1",  # MOST IMPORTANT - prevents log buffering
                    "RABBITMQ_HOST": os.getenv("RABBITMQ_HOST", "rabbitmq"),
                    "RABBITMQ_PORT": os.getenv("RABBITMQ_PORT", "5672"),
                    "RABBITMQ_USER": os.getenv("RABBITMQ_USER", "guest"),
                    "RABBITMQ_PASS": os.getenv("RABBITMQ_PASS", "guest"),
                    "QUEUE_NAME": os.getenv("QUEUE_NAME", "my-queue"),
                }                
                for env_key, env_value in essential_env_vars.items():
                    run_cmd += ["-e", f"{env_key}={env_value}"]
                # # optional: restart policy
                # run_cmd += ["--restart","unless-stopped"]
                run_cmd.append(IMAGE)
                subprocess.run(run_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"Started container {name}")
                # # 2. Connect to logging network separately
                # try:
                #     subprocess.run(
                #         ["docker", "network", "connect", "myapp_logging", name],
                #         check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                #     )
                #     logger.info(f"Connected {name} to logging network")
                # except subprocess.CalledProcessError as e:
                #     logger.warning(f"Failed to connect {name} to logging network: {e}")
                changed = True
            except FileNotFoundError:
                logger.error("ERROR: Docker CLI not found. Install docker-cli or use Docker SDK.")
                return False
            except subprocess.CalledProcessError as e:
                logger.error(f"ERROR: Failed to start container {name}: {e}")

    elif desired_count < current_count:
        scale_down = current_count - desired_count
        to_remove = current_workers[:scale_down]
        logger.info(f"Scaling DOWN: Removing {scale_down} workers")
        for cid in to_remove:
            try:
                subprocess.run(["docker","stop",f"--time={STOP_TIMEOUT}",cid],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["docker","rm",cid], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"Gracefully stopped & removed container {cid}")
                changed = True
            except FileNotFoundError:
                logger.error("ERROR: Docker CLI not found. Install docker-cli or use Docker SDK.")
                return False
            except subprocess.CalledProcessError as e:
                logger.error(f"ERROR: Failed to stop/remove container {cid}: {e}")

    return changed

def cleanup_dynamic_workers():
    try:
        # match both our owner label and the name prefix
        result = subprocess.run(
            ["docker","ps","-aq",
             "--filter", "label=autoscaler.owner=true",
             "--filter", f"name={CONTAINER_NAME_PREFIX}"],
            stdout=subprocess.PIPE, text=True, check=True
        )
        ids = [i for i in result.stdout.splitlines() if i]
        if ids:
            logger.info(f"Cleaning up {len(ids)} dynamic workers")
            for cid in ids:
                try:
                    subprocess.run(["docker","stop", f"--time={STOP_TIMEOUT}", cid],
                                check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(["docker","rm", cid],
                                check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
        else:
            logger.info("No dynamic workers to clean up")
        logger.info(f"Cleaned up {len(ids)} dynamic workers")
    except Exception as e:
        logger.error(f"ERROR: Cleanup failed: {e}")

def _handle_term(sig, frame):
    logger.info("Received termination signal; cleaning up dynamic workersâ€¦")
    cleanup_dynamic_workers()
    sys.exit(0)

def _handle_sigusr1(sig, frame):
    """Handle SIGUSR1 to cleanup workers without exiting (useful for docker-compose down)"""
    logger.info("Received SIGUSR1; cleaning up dynamic workers but staying alive...")
    print(f"[{CONTAINER_ID}] Cleaning up dynamic workers on request...", flush=True)
    cleanup_dynamic_workers()

signal.signal(signal.SIGTERM, _handle_term)
signal.signal(signal.SIGINT,  _handle_term)
signal.signal(signal.SIGUSR1, _handle_sigusr1)

# ========================
# MAIN LOOP
# ========================
def main():
    DOWN_STREAK = 0

    logger.info("RabbitMQ Docker Autoscaler started")
    ensure_queue_exists()

    last_scale_time = 0

    while True:
        queue_length = get_queue_length()
        logger.info(f"Queue length: {queue_length}")
        
        if queue_length <= SCALE_DOWN_THRESHOLD:
            DOWN_STREAK += 1
        else:
            DOWN_STREAK = 0

        current_workers = get_running_workers()
        current_count = len(current_workers)
        desired_count = max(current_count, MIN_CONTAINERS)

        if queue_length >= SCALE_UP_THRESHOLD and current_count < MAX_CONTAINERS:
            desired_count = min(MAX_CONTAINERS, max(MIN_CONTAINERS, math.ceil(queue_length / SAFE_MPW)))
        elif queue_length <= SCALE_DOWN_THRESHOLD and current_count > MIN_CONTAINERS:
            desired_count = max(MIN_CONTAINERS, math.ceil(queue_length / SAFE_MPW))
        elif DOWN_STREAK >= 3 and current_count > MIN_CONTAINERS:
            desired_count = max(MIN_CONTAINERS, math.ceil(queue_length / SAFE_MPW))

        now = time.time()
        if desired_count != current_count:
            if now - last_scale_time < COOLDOWN_PERIOD:
                logger.info("Cooldown active, skipping scale action")
            else:
                logger.info(f"Scaling from {current_count} to {desired_count} workers")
                changed = scale_workers(desired_count)
                if changed:
                    last_scale_time = now
                else:
                    logger.info("No containers changed; not starting cooldown so we can retry next poll.")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("ERROR: Autoscaler stopped by user")
        sys.exit(0)