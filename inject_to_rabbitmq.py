import json
import os
import sys
import yaml
import logging
from typing import Optional

import pika
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("rabbitmq-injector")

def get_rabbitmq_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
        
    rmq = cfg.get("rabbitmq", {})
    
    host = os.getenv("RABBITMQ_HOST", rmq.get("host", "localhost"))
    port = int(os.getenv("RABBITMQ_PORT", rmq.get("port", 5672)))
    vhost = os.getenv("RABBITMQ_VHOST", rmq.get("vhost", "/"))
    username = os.getenv("RABBITMQ_USERNAME", rmq.get("username", "guest"))
    password = os.getenv("RABBITMQ_PASSWORD", rmq.get("password", "guest"))
    queue_name = rmq.get("queue", "dnac.alerts.q")
    exchange = rmq.get("exchange", "")
    
    return {
        "host": host,
        "port": port,
        "vhost": vhost,
        "username": username,
        "password": password,
        "queue": queue_name,
        "exchange": exchange,
    }

def inject_file(filepath: str, rmq_cfg: Optional[dict] = None):
    if rmq_cfg is None:
        rmq_cfg = get_rabbitmq_config()
        
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        payloads = json.load(f)
        
    if isinstance(payloads, dict):
        payloads = [payloads]
        
    logger.info(f"Connecting to RabbitMQ {rmq_cfg['host']}:{rmq_cfg['port']} (vhost={rmq_cfg['vhost']})...")
    
    credentials = pika.PlainCredentials(rmq_cfg["username"], rmq_cfg["password"])
    parameters = pika.ConnectionParameters(
        host=rmq_cfg["host"],
        port=rmq_cfg["port"],
        virtual_host=rmq_cfg["vhost"],
        credentials=credentials,
    )
    
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    
    channel.queue_declare(queue=rmq_cfg["queue"], durable=True)
    
    logger.info(f"Publishing {len(payloads)} message(s) from '{filepath}' to queue '{rmq_cfg['queue']}'...")
    
    for i, payload in enumerate(payloads, start=1):
        event_id = payload.get("eventId") or payload.get("event_id") or f"MSG-{i}"
        body = json.dumps(payload, indent=2)
        
        channel.basic_publish(
            exchange=rmq_cfg["exchange"],
            routing_key=rmq_cfg["queue"],
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
                content_type="application/json",
            )
        )
        logger.info(f"  [{i}/{len(payloads)}] Successfully published alert '{event_id}'")
        
    connection.close()
    logger.info(f"Done! {len(payloads)} message(s) injected into RabbitMQ.\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        inject_file(target)
    else:
        logger.info("No file specified. Injecting all 3 datasets sequentially...\n")
        datasets = [
            "data/backdated_alerts.json",
            "data/auto_resolving_alerts.json",
            "data/non_auto_resolving_alerts.json",
        ]
        for ds in datasets:
            inject_file(ds)
