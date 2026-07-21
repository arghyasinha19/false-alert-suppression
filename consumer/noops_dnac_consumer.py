from __future__ import annotations
import sys
import json
import os
import signal
import time
import logging
from typing import Any, Dict, Optional, Tuple, Iterable, Union
import re

import pika
import requests
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------------------
# Load helpers/configs
# -------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, "helpers"))
sys.path.append(os.path.join(parent_dir, "mapping"))
sys.path.append(os.path.join(parent_dir, "config"))

from helpers.generic_helpers import *  # noqa
from helpers.jenkins_helpers import *  # noqa
from helpers.logger import *           # noqa
from helpers.rabbitmq_helpers import * # noqa
from helpers.snow_acknowledge import * # noqa
from config.rabbitmq import *          # noqa

logger = setup_file_logger(name="noops-dnac-consumer")

STOP = False
_CURRENT_CONNECTION = None
_CURRENT_CHANNEL = None

jenkins_base_url=os.getenv("JENKINS_URL")
jenkins_username=os.getenv("JENKINS_USERNAME")
jenkins_api_token=os.getenv("JENKINS_TOKEN")
jenkins_job_path = os.getenv("JENKINS_JOB_PATH")

def normalize_json_payload(
    payload: Union[Dict[str, Any], list],
    *,
    parent_key: str = "",
    sep: str = ".",
    sanitize_keys: bool = True,
    keep_none: bool = True,
    list_strategy: str = "index",
    join_list_sep: str = ",",
    collision_strategy: str = "suffix", # "suffix" or "overwrite" or "error"
) -> Dict[str, Any]:

    # Flattens a JSON-like structure (dict/list) into a single-level dict.
    def _sanitize_segment(seg: str) -> str:
        if not sanitize_keys:
            return seg
            
        # Replace whitespace with underscores
        seg = re.sub(r"\s+", "_", seg.strip())
        # Replace forward slashes to avoid path confusion in stores
        seg = seg.replace("/", "_")
        # Remove characters that are problematic in many sinks (optional)
        seg = re.sub(r"[^0-9a-zA-Z_\-\[\]]", "", seg)
        return seg

    def _add(out: Dict[str, Any], key: str, value: Any) -> None:
        if value is None and not keep_none:
            return
            
        if key not in out:
            out[key] = value
            return
            
        if collision_strategy == "overwrite":
            out[key] = value
            return
            
        if collision_strategy == "error":
            raise ValueError(f"Key collision detected for '{key}'")
            
        # collision_strategy == "suffix"
        i = 2
        new_key = f"{key}_{i}"
        while new_key in out:
            i += 1
            new_key = f"{key}_{i}"
        out[new_key] = value

    def _is_primitive(x: Any) -> bool:
        return isinstance(x, (str, int, float, bool)) or x is None
        
    def _flatten(obj: Any, prefix: str, out: Dict[str, Any]) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                seg = _sanitize_segment(str(k))
                new_prefix = f"{prefix}{sep}{seg}" if prefix else seg
                _flatten(v, new_prefix, out)
                
        elif isinstance(obj, list):
            if list_strategy == "join" and all(_is_primitive(x) for x in obj):
                joined = join_list_sep.join("" if x is None else str(x) for x in obj)
                _add(out, prefix if prefix else "[]", joined)
                return
                
            # default: index expansion
            for idx, item in enumerate(obj):
                new_prefix = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
                _flatten(item, new_prefix, out)
                
        else:
            # primitive or unknown object types
            _add(out, prefix if prefix else "value", obj)
            
    flattened: Dict[str, Any] = {}
    start_prefix = _sanitize_segment(parent_key) if parent_key else ""
    _flatten(payload, start_prefix, flattened)
    return flattened

def handle_signal(signum, frame):
    global STOP
    logger.info("Received signal %s, stopping...", signum)
    STOP = True
    # If blocked in connection, attempt to interrupt
    if _CURRENT_CONNECTION and _CURRENT_CONNECTION.is_open:
        _CURRENT_CONNECTION.sleep(0) # trigger heartbeat/interrupt

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def run():
    global _CURRENT_CONNECTION, _CURRENT_CHANNEL
    
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    conn_params = pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PORT,
        virtual_host=RABBIT_VHOST,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30,
        connection_attempts=5,
        retry_delay=5,
    )
    
    while not STOP:
        try:
            _CURRENT_CONNECTION = pika.BlockingConnection(conn_params)
            _CURRENT_CHANNEL = _CURRENT_CONNECTION.channel()
            
            _CURRENT_CHANNEL.basic_qos(prefetch_count=PREFETCH)
            _CURRENT_CHANNEL.confirm_delivery()
            
            logger.info("Connected. Consuming from %s on vhost %s", QUEUE_MAIN, RABBIT_VHOST)
            
            def on_message(ch, method, properties, body):
                if STOP:
                    try:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    finally:
                        try:
                            ch.stop_consuming()
                        except Exception:
                            pass
                    return
                    
                try:
                    payload = parse_json(body)
                    # event_type, ticket, meta = normalize_incoming(payload)
                    
                    logger.info(
                        "DNAC Payload from RabbitMQ:\n  Body: %s",
                        json.dumps(payload, indent=2) if isinstance(payload, (dict, list)) else str(payload)
                    )
                    
                    # Get meta data from the payload in a dictionary
                    normalized_payload = normalize_json_payload(payload)
                    
                    logger.info(
                        "DNAC Normalized Payload:\n  Body: %s",
                        json.dumps(normalized_payload, indent=2)
                    )
                    
                    retry_count = get_retry_count(properties) if properties else 0
                    logger.info("Received payload, retries=%s", retry_count)
                    
                    # Max retries -> DLQ, ACK original
                    if retry_count >= MAX_RETRIES:
                        dlq_headers = {"reason": "max_retries_exceeded", "retry_count": retry_count}
                        publish_with_confirm(
                            channel=ch,
                            exchange=EXCHANGE_DLQ,
                            routing_key=RK_DLQ,
                            body=body,
                            headers=dlq_headers,
                            correlation_id=getattr(properties, "correlation_id", None),
                            message_id=getattr(properties, "message_id", None)
                        )
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        logger.warning("Sent to DLQ after retries=%s", retry_count)
                        return
                        
                    cfg = JenkinsConfig(
                        base_url=jenkins_base_url,
                        username=jenkins_username,
                        api_token=jenkins_api_token,
                        verify_tls=False,
                    )
                    
                    jh = JenkinsHelper(cfg)
                    params = map_dnac_to_jenkins_params(normalized_payload)
                    
                    trigger_result = jh.trigger_parameterized_job(
                        job_path=jenkins_job_path,
                        params=params,
                        cause="Triggered by DNAC webhook automation",
                        retries=3
                    )
                    
                    if trigger_result.get("queue_url"):
                        build_info = jh.wait_for_build_number(trigger_result["queue_url"], timeout_sec=120)
                        logger.info("Created build %s successfully", build_info)
                        
                    # Success -> ACK message
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logger.info("Processed %s successfully", normalized_payload.get("eventId"))
                    
                except Exception as e:
                    logger.exception("Error processing message; will dead-letter to retry via NACK")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    
            _CURRENT_CHANNEL.basic_consume(queue=QUEUE_MAIN, on_message_callback=on_message, auto_ack=False)
            _CURRENT_CHANNEL.start_consuming()
            
        except pika.exceptions.AMQPConnectionError as e:
            if STOP:
                break
            logger.error("Connection error: %s. Retrying in 5s...", e)
            time.sleep(5)
            
        except Exception as e:
            if STOP:
                break
            logger.exception("Unexpected error: %s. Retrying in 5s...", e)
            time.sleep(5)
            
        finally:
            try:
                if _CURRENT_CHANNEL and _CURRENT_CHANNEL.is_open:
                    _CURRENT_CHANNEL.close()
            except Exception:
                pass
                
            try:
                if _CURRENT_CONNECTION and _CURRENT_CONNECTION.is_open:
                    _CURRENT_CONNECTION.close()
            except Exception:
                pass
                
            _CURRENT_CHANNEL = None
            _CURRENT_CONNECTION = None
            
    logger.info("Consumer stopped.")
    
if __name__ == "__main__":
    run()
