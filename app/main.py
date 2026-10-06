import yaml
import json
import hmac
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv, find_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# find_dotenv() walks UP from the CWD until it finds a .env file.
# override=False: real environment variables (e.g. injected by the
# orchestrator / secret manager) always win over .env.
load_dotenv(find_dotenv(), override=False)

from app.dnac_client import DNACClient, extract_issue_id
from app.mq_publisher import RabbitMQPublisher

# -------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Full payloads can be large and contain topology data; only log them at DEBUG.
LOG_FULL_PAYLOADS = os.getenv("LOG_FULL_PAYLOADS", "false").lower() in ("1", "true", "yes")

# -------------------------------------------------------------------------
# Config
# -------------------------------------------------------------------------
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')

def load_config() -> dict:
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# -------------------------------------------------------------------------
# Webhook authentication (shared secret sent by DNAC as a custom header,
# configured at subscription time - see DNACClient.register_webhook)
# -------------------------------------------------------------------------
WEBHOOK_AUTH_TOKEN = os.getenv("WEBHOOK_AUTH_TOKEN", "")
WEBHOOK_AUTH_HEADER = (
    config.get("dnac", {}).get("webhook_registration", {}).get("auth_header_name", "X-Webhook-Token")
)
ALLOW_UNAUTHENTICATED_WEBHOOK = os.getenv("ALLOW_UNAUTHENTICATED_WEBHOOK", "false").lower() in ("1", "true", "yes")

# -------------------------------------------------------------------------
# Clients
# -------------------------------------------------------------------------
dnac_client = DNACClient(config['dnac'])
mq_publisher = RabbitMQPublisher(config['rabbitmq'])

# -------------------------------------------------------------------------
# Lifespan: startup / shutdown hooks
# -------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Service starting up...")

    for var in ["DNAC_USERNAME", "DNAC_PASSWORD", "RABBITMQ_USERNAME", "RABBITMQ_PASSWORD"]:
        if os.environ.get(var):
            logger.info(f"  OK {var} is set")
        else:
            logger.warning(f"  X {var} is NOT set - check your environment/.env file!")

    if not WEBHOOK_AUTH_TOKEN:
        if ALLOW_UNAUTHENTICATED_WEBHOOK:
            logger.warning("WEBHOOK_AUTH_TOKEN not set and ALLOW_UNAUTHENTICATED_WEBHOOK=true: "
                           "webhook endpoint is OPEN. Do not run like this in production.")
        else:
            logger.error("WEBHOOK_AUTH_TOKEN not set: all webhook calls will be rejected (401). "
                         "Set the token, or ALLOW_UNAUTHENTICATED_WEBHOOK=true for local testing only.")

    try:
        dnac_client.authenticate()
        logger.info("DNAC token obtained. Service is ready.")
        logger.info("-> To register this service as a DNAC webhook receiver, call "
                    "POST /api/v1/subscriptions/register")
    except Exception as e:
        logger.error(f"Startup DNAC authentication failed: {e}")

    yield

    logger.info("Service shutting down...")
    mq_publisher.close()

# -------------------------------------------------------------------------
# App
# -------------------------------------------------------------------------
app = FastAPI(
    title="DNAC Webhook -> RabbitMQ Ingestion Service",
    description=(
        "Receives push-based alert events from Cisco DNA Center via webhook "
        "and publishes them to RabbitMQ for the false-alert ML pipeline."
    ),
    version="2.1.0",
    lifespan=lifespan
)

# Management endpoints (subscriptions) require this admin token.
ADMIN_API_TOKEN = os.getenv("INGEST_ADMIN_TOKEN", "")


def _token_ok(presented: str, expected: str) -> bool:
    return bool(expected) and bool(presented) and hmac.compare_digest(presented, expected)


def _require_webhook_auth(request: Request) -> None:
    if not WEBHOOK_AUTH_TOKEN and ALLOW_UNAUTHENTICATED_WEBHOOK:
        return
    presented = request.headers.get(WEBHOOK_AUTH_HEADER, "")
    if not _token_ok(presented, WEBHOOK_AUTH_TOKEN):
        logger.warning(f"Rejected webhook call from {request.client.host if request.client else '?'}: bad/missing token")
        raise HTTPException(status_code=401, detail="Unauthorized")


def _require_admin(request: Request) -> None:
    presented = request.headers.get("X-Admin-Token", "")
    if not _token_ok(presented, ADMIN_API_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized (X-Admin-Token required)")

# -------------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------------

@app.get("/health", tags=["Operations"])
def health_check():
    """Liveness probe for load balancers / k8s."""
    return {"status": "healthy", "service": "dnac-webhook-ingestion"}


async def _json_body(request: Request) -> Any:
    """Parse the JSON body; None if it is not valid JSON."""
    try:
        return await request.json()
    except Exception:
        return None


@app.post("/api/v1/webhook", tags=["Webhook"])
def dnac_webhook_receiver(request: Request, payload: Any = Depends(_json_body)):
    """
    The HTTP endpoint that Cisco DNAC pushes alert events to.

    Declared as a plain ``def`` so FastAPI runs it in a worker thread: the
    RabbitMQ publisher is blocking (with retries/back-off) and must not freeze
    the event loop.

    Returns 503 if ANY event could not be published, so DNAC retries rather
    than the alert being silently lost.
    """
    _require_webhook_auth(request)

    if payload is None:
        raise HTTPException(status_code=400, detail="Invalid or empty JSON payload received.")

    events = payload if isinstance(payload, list) else [payload]
    received_at = datetime.now(timezone.utc).isoformat()

    published = 0
    failed = 0
    for event in events:
        if not isinstance(event, dict):
            # Malformed input: retrying will not help, so don't return 503 for it.
            logger.warning(f"Skipping non-object event in webhook payload: {str(event)[:200]}")
            continue
        try:
            event['_source'] = "dnac-webhook"
            # Ingestion timestamp: used for backdate detection instead of the
            # (later) time Jenkins happens to run the workflow.
            event['_received_at'] = received_at
            # Carry the Assurance issueId (not the notification instanceId) so
            # the delayed check can query DNAC for the right issue.
            issue_id = extract_issue_id(event)
            if issue_id:
                event['issueId'] = issue_id

            if LOG_FULL_PAYLOADS:
                logger.info(f"DNAC webhook event: {json.dumps(event)}")

            mq_publisher.publish(event)
            published += 1
            logger.info(
                f"Published event to RabbitMQ | eventId={event.get('eventId', 'N/A')} | "
                f"instanceId={event.get('instanceId', 'N/A')} | issueId={issue_id or 'N/A'} | "
                f"severity={event.get('severity', 'N/A')} | "
                f"status={(event.get('details') or {}).get('Assurance Issue Status', 'N/A')}"
            )
        except Exception as e:
            failed += 1
            logger.error(f"Failed to publish event (eventId: {event.get('eventId', 'N/A')}): {e}")

    if failed:
        # Non-2xx tells DNAC the delivery failed so it can retry.
        return JSONResponse(
            status_code=503,
            content={"status": "partial_failure", "events_published": published, "events_failed": failed},
        )
    return JSONResponse(status_code=200, content={"status": "received", "events_published": published})

# -------------------------------------------------------------------------
# Webhook Management Endpoints (admin token required)
# -------------------------------------------------------------------------

@app.get("/api/v1/subscriptions", tags=["Webhook Management"])
def list_subscriptions(request: Request):
    """List all webhook/event subscriptions currently registered in DNAC."""
    _require_admin(request)
    try:
        subs = dnac_client.list_event_subscriptions()
        return {"total": len(subs), "subscriptions": subs}
    except Exception as e:
        logger.error(f"Failed to list subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/subscriptions/register", tags=["Webhook Management"])
def register_webhook(request: Request):
    """
    Register this service as a REST/Webhook subscriber in DNAC (idempotent by name).
    The subscription includes the WEBHOOK_AUTH_TOKEN header.
    """
    _require_admin(request)
    try:
        dnac_client.authenticate()
        result = dnac_client.register_webhook()
        return {"status": "registered", "subscription": result}
    except Exception as e:
        logger.error(f"Failed to register webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/subscriptions/deregister", tags=["Webhook Management"])
def deregister_webhook(request: Request):
    """Manually de-register this service's webhook subscription from DNAC."""
    _require_admin(request)
    try:
        if not dnac_client.subscription_id:
            subs = dnac_client.list_event_subscriptions()
            target_name = dnac_client.webhook_config.get('name', 'FalseAlertDetection')
            for sub in subs:
                if sub.get('name') == target_name:
                    dnac_client.subscription_id = sub.get('subscriptionId')
                    break

        if not dnac_client.subscription_id:
            return {
                "status": "not_found",
                "detail": "No active subscription found with the configured name. Nothing to deregister."
            }

        dnac_client.deregister_webhook()
        return {
            "status": "deregistered",
            "detail": "Webhook subscription removed from DNAC."
        }
    except Exception as e:
        logger.error(f"Failed to deregister webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
