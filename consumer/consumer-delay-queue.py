import os
import sys
import json
import yaml
import pika
import logging
import requests
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
# Ensure the root project directory is in sys.path so we can import 'workflow'
sys.path.insert(0, os.path.dirname(current_dir))

# Load environment variables from .env
load_dotenv()

# Configure logging using centralized logger
from workflow.utils.logger import configure_logging
logger = configure_logging()
logger = logging.getLogger("DelayedQueueConsumer")

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)



def process_delayed_alert(payload: dict):
    """
    Process the delayed alert:
    Forward the payload directly to the Delayed Jenkins Pipeline.
    The DNAC check and Agent 4 execution are handled inside the Jenkins job (run_delayed.py).
    """
    logger.info("Received delayed alert from wait queue. Forwarding to Delayed Jenkins Pipeline...")
    
    # Spin up Jenkins job to run the delayed workflow
    jenkins_base_url = os.getenv("JENKINS_URL")
    jenkins_username = os.getenv("JENKINS_USERNAME")
    jenkins_api_token = os.getenv("JENKINS_TOKEN")
    
    # Use the specific delayed job path, fallback to main if missing
    jenkins_job_path = os.getenv("JENKINS_DELAYED_JOB_PATH") or os.getenv("JENKINS_JOB_PATH")
    
    from helpers.jenkins_helpers import JenkinsConfig, JenkinsHelper
    
    try:
        cfg = JenkinsConfig(
            base_url=jenkins_base_url,
            username=jenkins_username,
            api_token=jenkins_api_token,
            verify_tls=False,
        )
        
        jh = JenkinsHelper(cfg)
        # The payload from Agent 3 is already formatted as AlertPayload (snake_case).
        # Convert keys to UPPERCASE for Jenkins parameters.
        params = {k.upper(): v for k, v in payload.items() if v is not None}
        
        # Add a flag if the workflow needs to know it's a delayed alert
        params["DELAYED_ALERT"] = "true"
        
        trigger_result = jh.trigger_parameterized_job(
            job_path=jenkins_job_path,
            params=params,
            cause="Triggered by DNAC Delayed Queue",
            retries=3
        )
        
        if trigger_result.get("queue_url"):
            logger.info(f"Delayed Jenkins job triggered successfully: {trigger_result['queue_url']}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to execute Delayed Jenkins Job: {e}", exc_info=True)
        return False

def callback(ch, method, properties, body):
    logger.info(f"Received delayed message.")
    try:
        payload = json.loads(body)
        success = process_delayed_alert(payload)
        
        if success:
            # Acknowledge the message if successfully processed or auto-resolved
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Message acknowledged.")
        else:
            # Drop the message without requeueing on failure to avoid infinite loop.
            logger.warning("Processing failed, rejecting message without requeue.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode message JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Unexpected error processing message: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    config = load_config()
    rmq_config = config.get("rabbitmq", {})
    delayed_config = rmq_config.get("delayed", {})
    
    host = rmq_config.get("host", "localhost")
    port = rmq_config.get("port", 5672)
    vhost = rmq_config.get("vhost", "/")
    
    # Authenticate via .env if credentials are provided
    rmq_user = os.getenv("RABBITMQ_USERNAME")
    rmq_pass = os.getenv("RABBITMQ_PASSWORD")
    
    if rmq_user and rmq_pass:
        credentials = pika.PlainCredentials(rmq_user, rmq_pass)
        parameters = pika.ConnectionParameters(host=host, port=port, virtual_host=vhost, credentials=credentials)
        logger.info("Using RabbitMQ credentials from .env")
    else:
        parameters = pika.ConnectionParameters(host=host, port=port, virtual_host=vhost)
        
    target_exchange = delayed_config.get("target_exchange", "dnac.exchange")
    target_routing_key = delayed_config.get("target_routing_key", "dnac.alerts.delayed")
    queue_name = "dnac.alerts.delayed.q"

    logger.info(f"Connecting to RabbitMQ at {host}:{port}{vhost}...")
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Ensure the exchange exists (typically direct exchange)
        channel.exchange_declare(exchange=target_exchange, exchange_type='direct', durable=True)
        
        # Declare the consumer queue
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Bind the queue to the target exchange with the DLX routing key
        channel.queue_bind(exchange=target_exchange, queue=queue_name, routing_key=target_routing_key)
        
        # Process one message at a time
        channel.basic_qos(prefetch_count=1)
        
        logger.info(f"Bound queue '{queue_name}' to exchange '{target_exchange}' with routing key '{target_routing_key}'")
        logger.info(' [*] Waiting for messages. To exit press CTRL+C')
        
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Consumer stopped manually.")
        try:
            connection.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
