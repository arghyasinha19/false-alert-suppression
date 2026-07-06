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
        self.username = config.get("username") or os.getenv("RABBITMQ_USERNAME", "guest")
        self.password = config.get("password") or os.getenv("RABBITMQ_PASSWORD", "guest")
        self.delayed_config = config.get("delayed", {})
        
    def _get_connection(self):
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials
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
        
        try:
            connection = self._get_connection()
            channel = connection.channel()
            
            # Declare the wait queue with DLX arguments
            channel.queue_declare(
                queue=wait_queue,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": target_exchange,
                    "x-dead-letter-routing-key": target_routing_key,
                    "x-message-ttl": delay_ms
                }
            )
            
            # Publish message directly to the wait queue
            channel.basic_publish(
                exchange="",
                routing_key=wait_queue,
                body=json.dumps(payload),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent
                )
            )
            
            logger.info(f"Published delayed message to {wait_queue}. Will trigger {target_routing_key} in {delay_ms} ms.")
            
            connection.close()
            return True
        except Exception as e:
            logger.error(f"Failed to publish delayed message to RabbitMQ: {e}")
            return False
