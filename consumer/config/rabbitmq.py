import os
from dotenv import load_dotenv
load_dotenv()

# -------------------------------------------------------------------------
# RabbitMQ config (match your setup)
# -------------------------------------------------------------------------
RABBIT_HOST = os.getenv("RABBIT_HOST", "10.208.130.50")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", "5672"))
RABBIT_VHOST = os.getenv("RABBIT_VHOST", "/noops_automation")
RABBIT_USER = os.getenv("RABBIT_USER", "svc_rabbitmq_noops_consumer")
RABBIT_PASS = os.getenv("RABBIT_PASS", "JustCheck@2025")

# QUEUE_MAIN = os.getenv("QUEUE_MAIN", "dnac.router.q")
QUEUE_MAIN = os.getenv("QUEUE_MAIN", "dnac_alerts")
# EXCHANGE_MAIN = os.getenv("EXCHANGE_MAIN", "dnac.exchange")
RK_MAIN = os.getenv("RK_MAIN", "router") # IMPORTANT: matches your binding output
EXCHANGE_UNMATCHED = os.getenv("EXCHANGE_UNMATCHED", "dnac.unmatched")
RK_UNMATCHED = os.getenv("RK_UNMATCHED", "unmatched")

EXCHANGE_DLQ = os.getenv("EXCHANGE_DLQ", "dnac.dlq")
RK_DLQ = os.getenv("RK_DLQ", "dlq")

PREFETCH = int(os.getenv("PREFETCH", "10"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
