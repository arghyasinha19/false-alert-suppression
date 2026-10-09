import os
import sys
import json
import asyncio
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import logging
from datetime import datetime, timezone, timedelta

# Ensure root dir and dashboard dir are in sys.path to prevent import errors
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(dashboard_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

from workflow.tools.mongodb_client import MongoDBClient

try:
    from dashboard.device_service import (
        fetch_device_telemetry,
        poll_device_live,
        get_empty_telemetry_dict,
        utc_now_iso,
    )
    from dashboard.dnac_monitor import _load_dnac_client
except ImportError:
    from device_service import (
        fetch_device_telemetry,
        poll_device_live,
        get_empty_telemetry_dict,
        utc_now_iso,
    )
    from dnac_monitor import _load_dnac_client

# Set up logging to both console and file
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "dashboard.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DashboardAPI")

app = FastAPI(title="False Alert Suppression API")

# Allow Vite React app to call this API
# Allowed browser origins (comma-separated). Default: local Vite dev server only.
CORS_ORIGINS = [o.strip() for o in os.getenv("DASHBOARD_CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo = MongoDBClient()


def safe_get(d, *keys, default=None):
    curr = d
    for k in keys:
        if not isinstance(curr, dict):
            return default
        curr = curr.get(k)
        if curr is None:
            return default
    return curr
def get_alert_records():
    """Fetch alerts from MongoDB."""
    collection = mongo.get_collection("alert_results")
    if collection is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        alerts = list(collection.find({}, {"_id": 0}))
        return alerts if alerts else []
    except Exception as e:
        logger.error(f"MongoDB query failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/api/alerts")
def get_alerts(response: Response):
    """Fetch all processed alerts from MongoDB or local simulated repository."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    alerts = get_alert_records()

    # Enrich with live ServiceNow statuses (best-effort — never blocks alerts)
    try:
        incident_numbers = set()
        for a in alerts:
            inc = safe_get(a, "results", "agent_4", "data", "incident")
            if inc and inc != "Unknown":
                incident_numbers.add(inc)

        snow_statuses = {}
        if incident_numbers:
            from workflow.tools.servicenow_client import ServiceNowClient
            snow_client = ServiceNowClient()
            snow_statuses = snow_client.get_incidents_by_numbers(list(incident_numbers))

        for a in alerts:
            inc = safe_get(a, "results", "agent_4", "data", "incident")
            if inc in snow_statuses:
                a["live_snow_status"] = snow_statuses[inc]
    except Exception as e:
        logger.warning(f"ServiceNow enrichment failed (alerts still returned): {e}")

    return {"alerts": alerts, "source": "mongodb"}


@app.post("/api/alerts/simulate")
def simulate_alert(count: int = 1, reset: bool = False):
    """Simulation disabled in production."""
    raise HTTPException(status_code=403, detail="Simulation disabled in production")


@app.get("/api/devices")
def get_devices(response: Response):
    """
    Return a unique list of devices with aggregated stats:
    latest status, total alert count, location (derived from name),
    active alerts, resolved alerts (split by dnac_live_status), etc.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    try:
        alerts = get_alert_records()
        device_map = {}

        for a in alerts:
            details = a.get("alert_details") or {}
            name = details.get("device_name") or details.get("device") or "Unknown"

            if name not in device_map:
                device_map[name] = {
                    "device_name": name,
                    "device_id": details.get("device_id", ""),
                    "location": _derive_location(name),
                    "total_alerts": 0,
                    "backdated": 0,
                    "auto_resolving": 0,
                    "non_auto_resolving": 0,
                    "snow_incidents": 0,
                    "last_alert_time": None,
                    "active_alerts": [],
                    "resolved_alerts": [],
                }

            entry = device_map[name]
            entry["total_alerts"] += 1

            is_backdated = safe_get(a, "results", "agent_1", "data", "is_backdated", default=False)
            predicted = safe_get(a, "results", "agent_2", "data", "predicted_category", default="")

            if is_backdated:
                entry["backdated"] += 1
            elif predicted == "Auto resolving":
                entry["auto_resolving"] += 1
            elif predicted == "Non-Auto Resolving":
                entry["non_auto_resolving"] += 1

            snow_action = safe_get(a, "results", "agent_4", "data", "action")
            if snow_action and "created" in str(snow_action):
                entry["snow_incidents"] += 1

            ts = details.get("timestamp") or details.get("raw_timestamp")
            if ts:
                entry["last_alert_time"] = ts

            # DNAC live status (written by dnac_sync.py)
            dnac_status = a.get("dnac_live_status")
            dnac_checked = a.get("dnac_last_checked")

            # Build the alert object with DNAC metadata
            alert_obj = {
                "event_id": details.get("event_id"),
                "severity": details.get("severity"),
                "issue_name": details.get("issue_name"),
                "issue_details": details.get("issue_details"),
                "category": details.get("category"),
                "timestamp": ts,
                "predicted_category": predicted if not is_backdated else "Backdated",
                "snow_incident": safe_get(a, "results", "agent_4", "data", "incident"),
                "snow_action": snow_action,
                "dnac_live_status": dnac_status,
                "dnac_last_checked": dnac_checked,
            }

            # Split into active vs resolved based on dnac_live_status
            if is_backdated:
                # Backdated alerts go into resolved
                entry["resolved_alerts"].append(alert_obj)
            elif dnac_status == "RESOLVED":
                entry["resolved_alerts"].append(alert_obj)
            else:
                # ACTIVE, UNCERTAIN, or not yet checked → active
                entry["active_alerts"].append(alert_obj)

        devices = list(device_map.values())

        # Enrich devices with cached telemetry metadata (hostname, site_name, model)
        if mongo:
            try:
                coll = mongo.get_collection("device_telemetry")
                if coll:
                    cached_records = {doc.get("device_name"): doc for doc in coll.find({}, {"device_name": 1, "device_info": 1})}
                    for d in devices:
                        cached = cached_records.get(d.get("device_name"))
                        if cached and cached.get("device_info"):
                            info = cached["device_info"]
                            if info.get("hostname"):
                                d["hostname"] = info["hostname"]
                            if info.get("site_name"):
                                d["site_name"] = info["site_name"]
                                if d.get("location") in ("Global Network", "Unknown", None):
                                    d["location"] = info["site_name"]
                            if info.get("model") and info.get("model") != "Unknown":
                                d["model"] = info["model"]
            except Exception as enrich_err:
                logger.debug(f"Telemetry cache enrichment in get_devices skipped: {enrich_err}")

        return {"devices": devices}
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        return {"devices": []}


@app.get("/api/device/{device_name}/history")
def get_device_history(device_name: str):
    """Return all historical alert records for a specific device."""
    collection = mongo.get_collection("alert_results")
    if collection is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        # Query by device_name in alert_details
        query = {
            "$or": [
                {"alert_details.device_name": device_name},
                {"alert_details.device": device_name},
            ]
        }
        alerts = list(collection.find(query, {"_id": 0}).sort("alert_details.timestamp", -1))
        return {"device_name": device_name, "alerts": alerts}
    except Exception as e:
        logger.error(f"Error fetching history for {device_name}: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


_dnac_client_instance = None


def get_dnac_client():
    global _dnac_client_instance
    if _dnac_client_instance is None:
        _dnac_client_instance = _load_dnac_client()
    return _dnac_client_instance


@app.get("/api/devices/{device_name}/telemetry")
@app.get("/api/device/{device_name}/telemetry")
def get_device_telemetry(device_name: str):
    """
    Fetch live Cisco DNA Center Assurance telemetry vitals (CPU, memory, packet drop,
    health score, interface errors, PoE, uptime) and hardware specifications for a device.
    Falls back gracefully to cached or offline records without throwing HTTP 500 errors.
    """
    try:
        client = get_dnac_client()
        return fetch_device_telemetry(device_name, mongo_client=mongo, dnac_client=client)
    except Exception as e:
        logger.error(f"Error handling telemetry endpoint for {device_name}: {e}")
        raise HTTPException(status_code=503, detail="Cisco DNA Center or telemetry cache unreachable")


@app.post("/api/devices/{device_name}/live-poll")
@app.post("/api/device/{device_name}/live-poll")
def live_poll_device(device_name: str):
    """
    Trigger on-demand live polling for a device:
    Synchronously re-checks active alerts in MongoDB against DNAC and refreshes
    live Assurance telemetry vitals.
    """
    try:
        client = get_dnac_client()
        return poll_device_live(device_name, mongo_client=mongo, dnac_client=client)
    except Exception as e:
        logger.error(f"Error handling live-poll endpoint for {device_name}: {e}")
        raise HTTPException(status_code=503, detail="Cisco DNA Center unreachable")


@app.get("/api/kpi/summary")
def get_kpi_summary():
    """
    Pre-computed aggregate KPIs for the dashboard:
    suppression rates, category volumes, hourly distribution, etc.
    """
    try:
        alerts = get_alert_records()
        total = len(alerts)

        backdated = 0
        auto_resolving = 0
        non_auto_resolving = 0
        uncertain = 0
        snow_created = 0
        snow_appended = 0
        snow_reopened = 0
        delayed_resolved = 0

        hourly_buckets = {}
        daily_buckets = {}
        device_counts = {}

        for a in alerts:
            details = a.get("alert_details") or {}
            
            is_bd = safe_get(a, "results", "agent_1", "data", "is_backdated", default=False)
            predicted = safe_get(a, "results", "agent_2", "data", "predicted_category", default="")
            snow_action = safe_get(a, "results", "agent_4", "data", "action", default="")

            if is_bd:
                backdated += 1
                cat = "Backdated"
            elif predicted == "Auto resolving":
                auto_resolving += 1
                cat = "Auto Resolving"
            elif predicted == "Non-Auto Resolving":
                non_auto_resolving += 1
                cat = "Non-Auto Resolving"
            else:
                uncertain += 1
                cat = "Uncertain"

            if snow_action == "incident_created":
                snow_created += 1
            elif snow_action == "comment_appended":
                snow_appended += 1
            elif snow_action == "incident_reopened":
                snow_reopened += 1

            delayed_status = safe_get(a, "results", "delayed_check", "status", default="")
            if delayed_status == "resolved":
                delayed_resolved += 1

            # Time bucketing
            ts = details.get("timestamp") or details.get("raw_timestamp")
            if ts:
                try:
                    if isinstance(ts, (int, float)):
                        if ts > 1e12:
                            dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                        else:
                            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    else:
                        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))

                    hour_key = dt.strftime("%Y-%m-%d %H:00")
                    day_key = dt.strftime("%Y-%m-%d")

                    hourly_buckets.setdefault(hour_key, {"Backdated": 0, "Auto Resolving": 0, "Non-Auto Resolving": 0, "Uncertain": 0})
                    hourly_buckets[hour_key][cat] += 1

                    daily_buckets.setdefault(day_key, {"Backdated": 0, "Auto Resolving": 0, "Non-Auto Resolving": 0, "Uncertain": 0})
                    daily_buckets[day_key][cat] += 1
                except Exception:
                    pass

            device = details.get("device_name") or details.get("device") or "Unknown"
            device_counts[device] = device_counts.get(device, 0) + 1

        suppression_rate = round(((backdated + auto_resolving) / total * 100), 1) if total > 0 else 0
        # Tickets avoided represents alerts where initial ticket creation was suppressed
        tickets_avoided = backdated + auto_resolving

        # Sort and format time series
        hourly_series = [{"time": k, **v} for k, v in sorted(hourly_buckets.items())]
        daily_series = [{"date": k, **v} for k, v in sorted(daily_buckets.items())]
        top_devices = sorted(device_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            "kpi": {
                "total_alerts": total,
                "backdated": backdated,
                "auto_resolving": auto_resolving,
                "non_auto_resolving": non_auto_resolving,
                "uncertain": uncertain,
                "suppression_rate": suppression_rate,
                "snow_tickets_created": snow_created,
                "snow_comments_appended": snow_appended,
                "snow_incidents_reopened": snow_reopened,
                "tickets_avoided": tickets_avoided,
                "delayed_resolved": delayed_resolved,
                "hourly_series": hourly_series,
                "daily_series": daily_series,
                "top_devices": [{"device": d, "count": c} for d, c in top_devices],
            }
        }
    except Exception as e:
        logger.error(f"Error computing KPI summary: {e}")
        return {"kpi": {}}


def _derive_location(device_name: str) -> str:
    """
    Derive a location label from the device naming convention.
    e.g. UK-LON-SW01 -> UK-LON, US-NY-RT02 -> US-NY, SG-SIN-FW01 -> SG-SIN
    """
    if not device_name or device_name == "Unknown":
        return "Unknown"

    parts = device_name.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return parts[0] if parts else "Unknown"


# -------------------------------------------------------------------------
# Alert Pattern Clustering endpoint
# -------------------------------------------------------------------------

_clustering_engine = None

def _get_clustering_engine():
    global _clustering_engine
    if _clustering_engine is None:
        try:
            from alert_clustering import AlertClusteringEngine
            _clustering_engine = AlertClusteringEngine()
            logger.info("AlertClusteringEngine initialised.")
        except Exception as e:
            logger.error(f"Failed to initialise AlertClusteringEngine: {e}")
    return _clustering_engine


def _build_volume_series(alerts, granularity="hourly"):
    """Build a time-bucketed volume series from all alerts."""
    buckets = {}
    cumulative = 0

    for a in alerts:
        details = a.get("alert_details") or {}
        results_data = a.get("results") or {}
        ts = details.get("timestamp") or details.get("raw_timestamp")
        if not ts:
            continue

        try:
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(
                    ts / 1000 if ts > 1e12 else ts, tz=timezone.utc
                )
            else:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            continue

        if granularity == "daily":
            key = dt.strftime("%Y-%m-%d")
        elif granularity == "weekly":
            # ISO week start
            key = dt.strftime("%Y-W%W")
        else:
            key = dt.strftime("%Y-%m-%d %H:00")

        if key not in buckets:
            buckets[key] = {
                "time": key,
                "Backdated": 0,
                "Auto Resolving": 0,
                "Non-Auto Resolving": 0,
                "Uncertain": 0,
                "total": 0,
            }

        is_bd = safe_get(a, "results", "agent_1", "data", "is_backdated", default=False)
        predicted = safe_get(a, "results", "agent_2", "data", "predicted_category", default="")

        if is_bd:
            buckets[key]["Backdated"] += 1
        elif predicted and predicted.lower() == "auto resolving":
            buckets[key]["Auto Resolving"] += 1
        elif predicted and predicted.lower() == "non-auto resolving":
            buckets[key]["Non-Auto Resolving"] += 1
        else:
            buckets[key]["Uncertain"] += 1

        buckets[key]["total"] += 1

    # Sort and add cumulative
    series = sorted(buckets.values(), key=lambda x: x["time"])
    cumulative = 0
    for entry in series:
        cumulative += entry["total"]
        entry["cumulative"] = cumulative

    return series


@app.get("/api/alerts/patterns")
def get_alert_patterns(granularity: str = "hourly"):
    """
    Cluster alerts by semantic similarity using sentence embeddings + HDBSCAN.
    Returns pattern clusters and volume time series.
    """
    try:
        alerts = get_alert_records()
    except Exception as e:
        logger.error(f"Error fetching alerts for patterns: {e}")
        return {"error": str(e), "patterns": [], "volume_series": []}

    # Cluster
    engine = _get_clustering_engine()
    if engine is not None:
        try:
            clusters = engine.cluster(alerts)
            patterns = [c.to_dict() for c in clusters]
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            patterns = []
    else:
        patterns = []

    # Volume series
    volume_series = _build_volume_series(alerts, granularity)

    return {
        "patterns": patterns,
        "volume_series": volume_series,
        "total_alerts": len(alerts),
        "total_patterns": len([p for p in patterns if not p.get("noise")]),
        "noise_count": len([p for p in patterns if p.get("noise")]),
    }


# -------------------------------------------------------------------------
# Chat endpoint
# -------------------------------------------------------------------------

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    SSE endpoint for the AI chat agent.

    Request body: {"message": str, "history": [{"role":str, "text":str}, ...]}

    Streams Server-Sent Events:
      {"type": "task",          "label": "Searching MongoDB..."}
      {"type": "clarification", "text": "...", "suggestions": [...]}
      {"type": "answer",        "text": "...", "citations": [...], "charts": [...]}
      {"type": "error",         "text": "..."}
      {"type": "done"}
    """
    try:
        body = await request.json()
    except Exception:
        return StreamingResponse(
            _sse_error("Invalid JSON request body."),
            media_type="text/event-stream",
        )

    user_message = body.get("message", "").strip()
    history = body.get("history", [])
    logger.info(f"Received Chat Message: '{user_message}' (history length: {len(history)})")

    if not user_message:
        return StreamingResponse(
            _sse_error("Message cannot be empty."),
            media_type="text/event-stream",
        )

    async def event_stream():
        task_events = []

        def on_task(label: str):
            task_events.append(label)

        # Run agent in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        try:
            try:
                from dashboard.chat_agent import ChatAgent
            except ImportError:
                from chat_agent import ChatAgent
            agent = ChatAgent()
        except Exception as e:
            yield _sse_encode({"type": "error", "text": str(e)})
            yield _sse_encode({"type": "done"})
            return

        # We run the synchronous agent in a thread pool
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        future = loop.run_in_executor(
            executor,
            lambda: agent.run(user_message, history=history, on_task=on_task),
        )

        # Poll for task events while agent is running
        sent_tasks = 0
        while not future.done():
            await asyncio.sleep(0.2)
            while sent_tasks < len(task_events):
                yield _sse_encode({"type": "task", "label": task_events[sent_tasks]})
                sent_tasks += 1

        # Flush remaining task events
        while sent_tasks < len(task_events):
            yield _sse_encode({"type": "task", "label": task_events[sent_tasks]})
            sent_tasks += 1

        try:
            result = future.result()
        except Exception as e:
            logger.error(f"Chat agent error: {e}")
            yield _sse_encode({"type": "error", "text": f"Agent error: {str(e)}"})
            yield _sse_encode({"type": "done"})
            return

        # Send result
        if result.get("clarification"):
            yield _sse_encode({
                "type": "clarification",
                "text": result["clarification"],
                "suggestions": result.get("suggestions", []),
            })
        else:
            yield _sse_encode({
                "type": "answer",
                "text": result.get("text", ""),
                "citations": result.get("citations", []),
                "charts": result.get("charts", []),
            })

        logger.info(f"Chat response completed for message: '{user_message}'")
        yield _sse_encode({"type": "done"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse_encode(data: dict) -> str:
    """Encode a dict as an SSE data line."""
    return f"data: {json.dumps(data, default=str)}\n\n"


def _sse_error(message: str):
    """Generator that yields a single error SSE event."""
    yield _sse_encode({"type": "error", "text": message})
    yield _sse_encode({"type": "done"})
