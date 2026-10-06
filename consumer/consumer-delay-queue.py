import os
import sys
import json
import time
import signal
import yaml
import pika
import pika.exceptions
import logging
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
# Ensure the root project directory is in sys.path so we can import 'workflow'
sys.path.insert(0, os.path.dirname(current_dir))

load_dotenv()

from workflow.utils.logger import configure_logging
configure_logging()
logger = logging.getLogger("DelayedQueueConsumer")

from helpers.jenkins_helpers import JenkinsConfig, JenkinsHelper, jenkins_verify_tls  # noqa: E402
from helpers.rabbitmq_helpers import publish_with_confirm  # noqa: E402

# Only these alert fields are forwarded to the Jenkins job (it declares exactly these parameters).
JENKINS_PARAM_KEYS = (
    "instance_id", "event_id", "device_id", "device_name", "severity", "category",
    "status", "raw_timestamp", "correlation_id", "source", "issue_name", "issue_details",
    "issue_id", "received_at",
)

EXCHANGE_DLQ = os.getenv("EXCHANGE_DLQ", "dnac.dlq")
RK_DLQ = os.getenv("RK_DLQ", "dlq")

STOP = False


def _handle_signal(signum, frame):
    global STOP
    logger.info("Received signal %s, stopping after current message...", signum)
    STOP = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def process_delayed_alert(payload: dict) -> bool:
    """
    Forward the delayed alert to the Delayed Jenkins Pipeline.
    The DNAC re-check and ServiceNow escalation happen inside that job.
    Returns True only if Jenkins accepted the trigger.
    """
    logger.info("Received delayed alert from wait queue. Forwarding to Delayed Jenkins Pipeline...")

    jenkins_job_path = os.getenv("JENKINS_DELAYED_JOB_PATH") or os.getenv("JENKINS_JOB_PATH")

    try:
        cfg = JenkinsConfig(
            base_url=os.getenv("JENKINS_URL"),
            username=os.getenv("JENKINS_USERNAME"),
            api_token=os.getenv("JENKINS_TOKEN"),
            verify_tls=jenkins_verify_tls(),
        )
        jh = JenkinsHelper(cfg)

        params = {k.upper(): payload.get(k) for k in JENKINS_PARAM_KEYS if payload.get(k) is not None}
        params["DELAYED_ALERT"] = "true"

        trigger_result = jh.trigger_parameterized_job(
            job_path=jenkins_job_path,
            params=params,
            cause="Triggered by DNAC Delayed Queue",
            retries=3,
        )
        # Jenkins answered 2xx: the job is queued (Location header is optional).
        if trigger_result.get("ok"):
            logger.info(f"Delayed Jenkins job triggered: {trigger_result.get('queue_url')}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to execute Delayed Jenkins Job: {e}", exc_info=True)
        return False


def _dead_letter(ch, body: bytes, reason: str) -> bool:
    """Park a message we could not process in the DLQ so it is never silently lost."""
    try:
        publish_with_confirm(
            channel=ch, exchange=EXCHANGE_DLQ, routing_key=RK_DLQ, body=body,
            headers={"reason": reason, "source_queue": "dnac.alerts.delayed.q"},
        )
        logger.warning(f"Delayed alert sent to DLQ ({EXCHANGE_DLQ}/{RK_DLQ}): {reason}")
        return True
    except Exception as e:
        logger.error(f"Could not publish to DLQ: {e}")
        return False


def callback(ch, method, properties, body):
    logger.info("Received delayed message.")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode message JSON: {e}")
        if _dead_letter(ch, body, f"invalid_json: {e}"):
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        return

    if process_delayed_alert(payload):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("Message acknowledged.")
        return

    # Jenkins trigger failed: do NOT drop the alert (previously nack/requeue=False
    # on a queue with no DLX deleted it). Park it in the DLQ, or requeue.
    if _dead_letter(ch, body, "jenkins_trigger_failed"):
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        time.sleep(5)  # avoid a hot requeue loop
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main():
    config = load_config()
    rmq_config = config.get("rabbitmq", {})
    delayed_config = rmq_config.get("delayed", {})

    host = rmq_config.get("host", "localhost")
    port = rmq_config.get("port", 5672)
    vhost = rmq_config.get("vhost", "/")

    rmq_user = os.getenv("RABBITMQ_USERNAME")
    rmq_pass = os.getenv("RABBITMQ_PASSWORD")
    if not rmq_user or not rmq_pass:
        logger.error("RABBITMQ_USERNAME / RABBITMQ_PASSWORD not set.")
        sys.exit(1)

    parameters = pika.ConnectionParameters(
        host=host, port=port, virtual_host=vhost,
        credentials=pika.PlainCredentials(rmq_user, rmq_pass),
        heartbeat=60, blocked_connection_timeout=30,
        connection_attempts=5, retry_delay=5,
    )

    target_exchange = delayed_config.get("target_exchange", "dnac.exchange")
    target_routing_key = delayed_config.get("target_routing_key", "dnac.alerts.delayed")
    queue_name = delayed_config.get("consumer_queue", "dnac.alerts.delayed.q")
    declare_topology = bool(delayed_config.get("declare_topology", True))

    # Reconnect loop: previously any broker blip during consume killed the process.
    while not STOP:
        connection = None
        try:
            logger.info(f"Connecting to RabbitMQ at {host}:{port}{vhost}...")
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.confirm_delivery()

            if declare_topology:
                channel.exchange_declare(exchange=target_exchange, exchange_type='direct', durable=True)
                channel.queue_declare(queue=queue_name, durable=True)
                channel.queue_bind(exchange=target_exchange, queue=queue_name, routing_key=target_routing_key)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
            logger.info(f"Consuming from '{queue_name}'")
            while not STOP:
                connection.process_data_events(time_limit=1)
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"RabbitMQ connection error: {e}. Reconnecting in 5s...")
            time.sleep(5)
        except Exception as e:
            logger.exception(f"Unexpected consumer error: {e}. Reconnecting in 5s...")
            time.sleep(5)
        finally:
            try:
                if connection and connection.is_open:
                    connection.close()
            except Exception:
                pass

    logger.info("Delayed consumer stopped.")


if __name__ == "__main__":
    main()
