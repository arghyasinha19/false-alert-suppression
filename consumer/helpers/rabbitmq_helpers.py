import time
from typing import Any, Dict, Optional
import pika
from dotenv import load_dotenv
load_dotenv()

def get_retry_count(properties: pika.BasicProperties) -> int:
    """
    RabbitMQ adds x-death header when a message is dead-lettered.
    We'll compute retries from x-death counts if present.
    """
    headers = (properties.headers or {})
    x_death = headers.get("x-death")
    if not x_death:
        return 0
        
    # x-death is usually a list of dictionaries; sum counts
    # Example item: {"count": 3, "queue": "tickets.router.q", ...}
    try:
        return int(sum(item.get("count", 0) for item in x_death if isinstance(item, dict)))
    except Exception:
        return 0

def publish_with_confirm(channel: pika.channel.Channel, exchange: str, routing_key: str, body: bytes,
                         headers: Optional[Dict[str, Any]] = None,
                         correlation_id: Optional[str] = None,
                         message_id: Optional[str] = None) -> None:
    """
    Publish and require broker confirmation (publisher confirms).
    """
    props = pika.BasicProperties(
        content_type="application/json",
        content_encoding="utf-8",
        delivery_mode=2,
        headers=headers or {},
        correlation_id=correlation_id,
        message_id=message_id,
        timestamp=int(time.time()),
        app_id="noops-dnac-consumer"
    )
    
    ok = channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=body,
        properties=props,
        mandatory=False
    )
    
    # With confirm_delivery enabled, basic_publish returns True/False for confirmation result
    if ok is False:
        raise RuntimeError(f"Publish not confirmed to {exchange}:{routing_key}")
