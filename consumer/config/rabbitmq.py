import os
import yaml
from dotenv import load_dotenv

# Locate config.yaml in the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
consumer_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(consumer_dir)

# Load environment variables from the root .env
load_dotenv(os.path.join(root_dir, '.env'))

# Load the central config.yaml
config_path = os.path.join(root_dir, 'config.yaml')
try:
    with open(config_path, 'r') as f:
        app_config = yaml.safe_load(f)
except FileNotFoundError:
    app_config = {}

rabbit_config = app_config.get('rabbitmq', {})

# -------------------------------------------------------------------------
# RabbitMQ config (match your setup)
# -------------------------------------------------------------------------
RABBIT_HOST = rabbit_config.get("host", "localhost")
RABBIT_PORT = int(rabbit_config.get("port", 5672))
RABBIT_VHOST = rabbit_config.get("vhost", "/noops_automation")

# Credentials MUST come from the environment / secret store. No defaults:
# a hard-coded password in source is a security incident.
RABBIT_USER = os.getenv("RABBITMQ_USERNAME") or os.getenv("RABBIT_USER")
RABBIT_PASS = os.getenv("RABBITMQ_PASSWORD") or os.getenv("RABBIT_PASS")
if not RABBIT_USER or not RABBIT_PASS:
    raise RuntimeError(
        "RabbitMQ credentials missing. Set RABBITMQ_USERNAME and RABBITMQ_PASSWORD "
        "(environment or .env)."
    )

QUEUE_MAIN = rabbit_config.get("queue", "dnac.alerts.q")
EXCHANGE_MAIN = rabbit_config.get("exchange", "dnac.exchange")

RK_MAIN = os.getenv("RK_MAIN", "router") # IMPORTANT: matches your binding output
EXCHANGE_UNMATCHED = os.getenv("EXCHANGE_UNMATCHED", "dnac.unmatched")
RK_UNMATCHED = os.getenv("RK_UNMATCHED", "unmatched")

EXCHANGE_DLQ = os.getenv("EXCHANGE_DLQ", "dnac.dlq")
RK_DLQ = os.getenv("RK_DLQ", "dlq")

PREFETCH = int(os.getenv("PREFETCH", "10"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
