import pika
import pika.exceptions
import json
import logging
import os
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 1


class RabbitMQPublisher:
    """
    RabbitMQ publisher with reconnection, publisher confirms and
    unroutable-message detection.

    - Publisher confirms (``confirm_delivery``) + ``mandatory=True``: a publish
      only counts as successful once the broker has accepted AND routed it to
      a queue. Previously, a routing-key/binding mismatch silently dropped
      every alert while the webhook still returned 200.
    - The routing key is configurable (``rabbitmq.routing_key``) and must match
      the binding of the main queue on ``rabbitmq.exchange``.
    - A lock serialises publishes because pika's BlockingConnection is not
      thread-safe and the webhook handler now runs in a thread pool.
    """

    def __init__(self, config: dict):
        self.host = config['host']
        self.port = config.get('port', 5672)
        self.username = os.environ.get('RABBITMQ_USERNAME') or config.get('username')
        self.password = os.environ.get('RABBITMQ_PASSWORD') or config.get('password')
        if not self.username or not self.password:
            raise ValueError("RabbitMQ credentials missing. Set RABBITMQ_USERNAME and RABBITMQ_PASSWORD.")
        self.vhost = config.get('vhost', '/')
        self.exchange = config.get('exchange', '')
        self.queue_name = config.get('queue', 'dnac.alerts.q')
        # Routing key: explicit config/env wins; default exchange routes by queue name.
        self.routing_key = (
            os.environ.get('RABBITMQ_ROUTING_KEY')
            or config.get('routing_key')
            or self.queue_name
        )
        self.declare_queue = bool(config.get('declare_queue', False))

        self._connection: Optional[pika.BlockingConnection] = None
        self._channel = None
        self._lock = threading.Lock()

    def _connect(self) -> None:
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
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        self._channel.confirm_delivery()

        if self.declare_queue:
            # Only if the service account has 'configure' permission.
            self._channel.queue_declare(queue=self.queue_name, durable=True)

        logger.info(
            f"RabbitMQ connected. exchange='{self.exchange}' routing_key='{self.routing_key}' "
            f"(publisher confirms ON, mandatory ON)"
        )

    def _is_connected(self) -> bool:
        return (
            self._connection is not None
            and not self._connection.is_closed
            and self._channel is not None
            and self._channel.is_open
        )

    def _reset(self) -> None:
        try:
            if self._connection and not self._connection.is_closed:
                self._connection.close()
        except Exception:
            pass
        self._connection = None
        self._channel = None

    def publish(self, message: dict) -> None:
        """
        Publish one JSON message. Raises RuntimeError if it could not be
        confirmed AND routed after MAX_RETRIES attempts.
        """
        body = json.dumps(message, default=str)
        properties = pika.BasicProperties(
            delivery_mode=2,
            content_type='application/json',
            message_id=str(message.get('instanceId') or message.get('eventId') or ''),
        )

        last_error = None
        with self._lock:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    if not self._is_connected():
                        self._connect()
                    self._channel.basic_publish(
                        exchange=self.exchange,
                        routing_key=self.routing_key,
                        body=body,
                        properties=properties,
                        mandatory=True,
                    )
                    return
                except pika.exceptions.UnroutableError as e:
                    # Broker accepted it but no queue is bound for this routing
                    # key: a configuration error, retrying will not help.
                    self._reset()
                    raise RuntimeError(
                        f"Message unroutable: exchange='{self.exchange}' routing_key='{self.routing_key}'. "
                        f"Check the queue binding / rabbitmq.routing_key. ({e})"
                    ) from e
                except (
                    pika.exceptions.NackError,
                    pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError,
                    pika.exceptions.StreamLostError,
                    ConnectionResetError,
                    OSError,
                ) as e:
                    last_error = e
                    delay = RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
                    logger.warning(
                        f"RabbitMQ publish failed (attempt {attempt}/{MAX_RETRIES}): {e!r}. Retrying in {delay}s..."
                    )
                    self._reset()
                    if attempt < MAX_RETRIES:
                        time.sleep(delay)

        raise RuntimeError(f"Failed to publish message to RabbitMQ after {MAX_RETRIES} attempts: {last_error!r}")

    def close(self) -> None:
        """Gracefully close the connection."""
        with self._lock:
            if self._connection and not self._connection.is_closed:
                try:
                    self._connection.close()
                    logger.info("RabbitMQ connection closed.")
                except Exception as e:
                    logger.warning(f"Error closing RabbitMQ connection: {e}")
