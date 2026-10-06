import pika
import json
import os
import logging

logger = logging.getLogger(__name__)

class RabbitMQBroker:
    def __init__(self, config: dict):
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 5672)
        self.vhost = config.get("vhost", "/")
        self.username = os.getenv("RABBITMQ_USERNAME") or config.get("username")
        self.password = os.getenv("RABBITMQ_PASSWORD") or config.get("password")
        self.delayed_config = config.get("delayed", {})
        
    def _get_connection(self):
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=30,
            socket_timeout=10,
        )
        return pika.BlockingConnection(parameters)
        
    def publish_delayed_message(self, payload: dict) -> bool:
        if not self.delayed_config:
            logger.error("No delayed queue config found in rabbitmq settings.")
            return False
            
        wait_queue = self.delayed_config.get("wait_queue", "dnac.alerts.wait.q")
        target_exchange = self.delayed_config.get("target_exchange", "dnac.exchange")
        target_routing_key = self.delayed_config.get("target_routing_key", "dnac.alerts.delayed")
        delay_ms = self.delayed_config.get("delay_ms", 900000)
        
        connection = None
        try:
            connection = self._get_connection()
            channel = connection.channel()
            # Publisher confirms: only report success once the broker has the message.
            channel.confirm_delivery()

            if self.delayed_config.get("declare_topology", True):
                # Declare the wait queue with DLX arguments (must match the
                # existing queue's arguments exactly, or the broker rejects it).
                channel.queue_declare(
                    queue=wait_queue,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": target_exchange,
                        "x-dead-letter-routing-key": target_routing_key,
                        "x-message-ttl": delay_ms
                    }
                )

            channel.basic_publish(
                exchange="",
                routing_key=wait_queue,
                body=json.dumps(payload, default=str),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent,
                    content_type="application/json",
                ),
                mandatory=True,
            )

            logger.info(f"Published delayed message to {wait_queue}. Will trigger {target_routing_key} in {delay_ms} ms.")
            return True
        except Exception as e:
            logger.error(f"Failed to publish delayed message to RabbitMQ: {e!r}")
            return False
        finally:
            try:
                if connection is not None and connection.is_open:
                    connection.close()
            except Exception:
                pass
