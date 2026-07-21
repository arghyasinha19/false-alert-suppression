"""
Chat Agent — Gemini-powered tool-calling agent for DNAC Ops queries.

Orchestrates:
  1. Intent analysis (TEXT_ONLY / VISUALIZATION / AMBIGUOUS)
  2. Tool-calling loop (MongoDB first, then DNAC)
  3. Citation collection
  4. Chart spec generation (via generate_visualization tool)
"""

import os
import sys
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

# ---- path setup ----
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

load_dotenv(os.path.join(_project_root, ".env"))

from workflow.tools.mongodb_client import MongoDBClient
from app.dnac_client import DNACClient

import yaml

logger = logging.getLogger("chat_agent")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_CA_BUNDLE = os.getenv("GEMINI_CA_BUNDLE", "")  # Path to root CA .pem file
# Resolve relative paths against the project root
if GEMINI_CA_BUNDLE and not os.path.isabs(GEMINI_CA_BUNDLE):
    GEMINI_CA_BUNDLE = os.path.join(_project_root, GEMINI_CA_BUNDLE)

# Set it globally for both requests library and Python ssl module
if GEMINI_CA_BUNDLE:
    os.environ["REQUESTS_CA_BUNDLE"] = GEMINI_CA_BUNDLE
    os.environ["SSL_CERT_FILE"] = GEMINI_CA_BUNDLE

_config_path = os.path.join(_project_root, "config.yaml")
with open(_config_path, "r") as _f:
    _config = yaml.safe_load(_f)

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _get_mongo() -> MongoDBClient:
    return MongoDBClient()


def _get_dnac() -> DNACClient:
    return DNACClient(_config["dnac"])


def tool_query_alerts(args: dict) -> dict:
    """Query MongoDB alert_results with optional filters."""
    mongo = _get_mongo()
    collection = mongo.get_collection("alert_results")
    if collection is None:
        return {"error": "MongoDB not connected", "results": []}

    query = {}
    if args.get("device_name"):
        query["$or"] = [
            {"alert_details.device_name": {"$regex": args["device_name"], "$options": "i"}},
            {"alert_details.device": {"$regex": args["device_name"], "$options": "i"}},
        ]
    if args.get("severity"):
        query["alert_details.severity"] = args["severity"]
    if args.get("category"):
        query["alert_details.category"] = {"$regex": args["category"], "$options": "i"}
    if args.get("event_id"):
        query["alert_details.event_id"] = args["event_id"]
    if args.get("status"):
        query["alert_details.status"] = {"$regex": args["status"], "$options": "i"}

    limit = min(int(args.get("limit", 20)), 100)

    results = list(collection.find(query, {"_id": 0}).sort("alert_details.timestamp", -1).limit(limit))
    return {
        "count": len(results),
        "query_used": json.dumps(query, default=str),
        "results": results,
    }


def tool_get_device_status(args: dict) -> dict:
    """Aggregate current device status from MongoDB."""
    mongo = _get_mongo()
    collection = mongo.get_collection("alert_results")
    if collection is None:
        return {"error": "MongoDB not connected"}

    device_name = args.get("device_name", "")
    query = {
        "$or": [
            {"alert_details.device_name": {"$regex": device_name, "$options": "i"}},
            {"alert_details.device": {"$regex": device_name, "$options": "i"}},
        ]
    }
    alerts = list(collection.find(query, {"_id": 0}))

    if not alerts:
        return {"device_name": device_name, "found": False, "message": "No alerts found for this device."}

    backdated = 0
    auto_resolving = 0
    non_auto_resolving = 0
    active_alerts = []
    latest_ts = None

    for a in alerts:
        details = a.get("alert_details") or {}
        results = a.get("results") or {}
        
        agent_1_data = (results.get("agent_1") or {}).get("data") or {}
        is_bd = agent_1_data.get("is_backdated", False)
        
        agent_2_data = (results.get("agent_2") or {}).get("data") or {}
        predicted = agent_2_data.get("predicted_category", "")

        if is_bd:
            backdated += 1
        elif predicted == "Auto resolving":
            auto_resolving += 1
        elif predicted == "Non-Auto Resolving":
            non_auto_resolving += 1

        ts = details.get("timestamp") or details.get("raw_timestamp")
        if ts and (latest_ts is None or ts > latest_ts):
            latest_ts = ts

        status_str = str(details.get("status", "")).lower()
        if status_str == "active" or not is_bd:
            active_alerts.append({
                "event_id": details.get("event_id"),
                "severity": details.get("severity"),
                "issue_name": details.get("issue_name"),
                "category": details.get("category"),
                "timestamp": ts,
                "predicted": predicted if not is_bd else "Backdated",
            })

    return {
        "device_name": device_name,
        "found": True,
        "total_alerts": len(alerts),
        "backdated": backdated,
        "auto_resolving": auto_resolving,
        "non_auto_resolving": non_auto_resolving,
        "active_alert_count": len(active_alerts),
        "active_alerts": active_alerts[:10],
        "last_alert_time": latest_ts,
    }


def tool_get_device_history(args: dict) -> dict:
    """Fetch historical alerts for a specific device."""
    mongo = _get_mongo()
    collection = mongo.get_collection("alert_results")
    if collection is None:
        return {"error": "MongoDB not connected", "alerts": []}

    device_name = args.get("device_name", "")
    limit = min(int(args.get("limit", 20)), 50)

    query = {
        "$or": [
            {"alert_details.device_name": {"$regex": device_name, "$options": "i"}},
            {"alert_details.device": {"$regex": device_name, "$options": "i"}},
        ]
    }
    alerts = list(collection.find(query, {"_id": 0}).sort("alert_details.timestamp", -1).limit(limit))
    return {"device_name": device_name, "count": len(alerts), "alerts": alerts}


def tool_get_kpi_summary(args: dict) -> dict:
    """Retrieve aggregate KPIs."""
    mongo = _get_mongo()
    collection = mongo.get_collection("alert_results")
    if collection is None:
        return {"error": "MongoDB not connected"}

    alerts = list(collection.find({}, {"_id": 0}))
    total = len(alerts)

    backdated = auto_resolving = non_auto_resolving = uncertain = 0
    snow_created = snow_appended = delayed_resolved = 0
    daily_buckets: Dict[str, Dict[str, int]] = {}
    device_counts: Dict[str, int] = {}
    severity_counts: Dict[str, int] = {}

    for a in alerts:
        details = a.get("alert_details") or {}
        results = a.get("results") or {}

        is_bd = ((results.get("agent_1") or {}).get("data") or {}).get("is_backdated", False)
        predicted = ((results.get("agent_2") or {}).get("data") or {}).get("predicted_category", "")
        snow_action = ((results.get("agent_4") or {}).get("data") or {}).get("action", "")

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

        delayed_status = (results.get("delayed_check") or {}).get("status", "")
        if delayed_status == "resolved":
            delayed_resolved += 1

        # Severity counts
        sev = str(details.get("severity", "Unknown"))
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Daily bucketing
        ts = details.get("timestamp") or details.get("raw_timestamp")
        if ts:
            try:
                if isinstance(ts, (int, float)):
                    dt = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts, tz=timezone.utc)
                else:
                    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                day_key = dt.strftime("%Y-%m-%d")
                daily_buckets.setdefault(day_key, {"Backdated": 0, "Auto Resolving": 0, "Non-Auto Resolving": 0, "Uncertain": 0})
                daily_buckets[day_key][cat] += 1
            except Exception:
                pass

        device = details.get("device_name") or details.get("device") or "Unknown"
        device_counts[device] = device_counts.get(device, 0) + 1

    suppression_rate = round(((backdated + auto_resolving) / total * 100), 1) if total > 0 else 0
    tickets_avoided = backdated + auto_resolving + delayed_resolved

    daily_series = [{"date": k, **v} for k, v in sorted(daily_buckets.items())]
    top_devices = sorted(device_counts.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "total_alerts": total,
        "backdated": backdated,
        "auto_resolving": auto_resolving,
        "non_auto_resolving": non_auto_resolving,
        "uncertain": uncertain,
        "suppression_rate": suppression_rate,
        "tickets_avoided": tickets_avoided,
        "snow_tickets_created": snow_created,
        "snow_comments_appended": snow_appended,
        "delayed_resolved": delayed_resolved,
        "severity_counts": severity_counts,
        "daily_series": daily_series,
        "top_devices": [{"device": d, "count": c} for d, c in top_devices],
    }


def tool_query_dnac_issue(args: dict) -> dict:
    """Live query DNAC for issue status by instanceId."""
    instance_id = args.get("instance_id", "")
    if not instance_id:
        return {"error": "instance_id is required"}

    try:
        client = _get_dnac()
        status = client.get_issue_status(instance_id)
        return {
            "instance_id": instance_id,
            "status": status,
            "source": "dnac_live_api",
            "endpoint": f"{client.base_url}/dna/intent/api/v1/issues/{instance_id}",
        }
    except Exception as e:
        return {"instance_id": instance_id, "error": str(e)}


def tool_query_dnac_device_health(args: dict) -> dict:
    """Live query DNAC for device health."""
    device_id = args.get("device_id", "")
    device_name = args.get("device_name", "")

    if not device_id and not device_name:
        return {"error": "device_id or device_name is required"}

    try:
        client = _get_dnac()
        # DNAC device health endpoint
        url = f"{client.base_url}/dna/intent/api/v1/device-health"
        params = {}
        if device_name:
            params["deviceName"] = device_name
        if device_id:
            params["deviceUuid"] = device_id

        logger.info(f"DNAC Request:\n  Method: GET\n  URL: {url}\n  Params: {json.dumps(params)}")
        response = requests.get(url, headers=client._get_headers(), params=params, verify=client.verify_ssl)
        logger.info(f"DNAC Response:\n  Status Code: {response.status_code}\n  Body: {response.text[:2000]}")

        if not response.ok:
            return {"error": f"DNAC returned {response.status_code}: {response.text[:500]}"}

        data = response.json()
        return {
            "source": "dnac_live_api",
            "endpoint": url,
            "device_health": data.get("response", data),
        }
    except Exception as e:
        return {"error": str(e)}


def tool_generate_visualization(args: dict) -> dict:
    """Pass-through tool — returns the chart spec as-is for frontend rendering."""
    return {
        "chart_type": args.get("chart_type", "bar"),
        "title": args.get("title", ""),
        "data": args.get("data", []),
        "x_key": args.get("x_key", "label"),
        "y_key": args.get("y_key", "value"),
        "colors": args.get("colors", []),
        "multi_series_keys": args.get("multi_series_keys", []),
    }


# ---------------------------------------------------------------------------
# Tool registry + Gemini function declarations
# ---------------------------------------------------------------------------
TOOLS = {
    "query_alerts": tool_query_alerts,
    "get_device_status": tool_get_device_status,
    "get_device_history": tool_get_device_history,
    "get_kpi_summary": tool_get_kpi_summary,
    "query_dnac_issue": tool_query_dnac_issue,
    "query_dnac_device_health": tool_query_dnac_device_health,
    "generate_visualization": tool_generate_visualization,
}

TOOL_TASK_LABELS = {
    "query_alerts": "Searching MongoDB for alerts...",
    "get_device_status": "Fetching device status from MongoDB...",
    "get_device_history": "Loading device history from MongoDB...",
    "get_kpi_summary": "Computing KPI summary from MongoDB...",
    "query_dnac_issue": "Querying DNAC for live issue status...",
    "query_dnac_device_health": "Querying DNAC for device health...",
    "generate_visualization": "Generating visualization...",
}

GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "query_alerts",
        "description": "Query the MongoDB alert_results collection for alert records. Use filters to narrow results. Returns alert details, classification results, and ServiceNow actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_name": {"type": "string", "description": "Filter by device name (partial match, case-insensitive)"},
                "severity": {"type": "integer", "description": "Filter by severity level (1=critical, 2=error, 3=warning)"},
                "category": {"type": "string", "description": "Filter by alert category (e.g. ERROR, WARN)"},
                "event_id": {"type": "string", "description": "Filter by specific event ID"},
                "status": {"type": "string", "description": "Filter by alert status (e.g. active)"},
                "limit": {"type": "integer", "description": "Max results to return (default 20, max 100)"},
            },
        },
    },
    {
        "name": "get_device_status",
        "description": "Get the current aggregated status for a specific network device from MongoDB. Returns total alerts, backdated/auto-resolving/non-auto-resolving counts, and active alerts.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_name": {"type": "string", "description": "The device name to look up"},
            },
            "required": ["device_name"],
        },
    },
    {
        "name": "get_device_history",
        "description": "Fetch historical alert records for a specific device from MongoDB, sorted newest-first.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_name": {"type": "string", "description": "The device name"},
                "limit": {"type": "integer", "description": "Max alerts to return (default 20)"},
            },
            "required": ["device_name"],
        },
    },
    {
        "name": "get_kpi_summary",
        "description": "Get aggregate KPI metrics: total alerts, suppression rate, category breakdown, daily trends, severity distribution, top devices. Use this for dashboard-level questions.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "query_dnac_issue",
        "description": "Query DNAC live API for the current status of a specific issue by its instanceId. Use ONLY when MongoDB does not have the answer or the user explicitly asks to check DNAC.",
        "parameters": {
            "type": "object",
            "properties": {
                "instance_id": {"type": "string", "description": "The DNAC issue instanceId (UUID)"},
            },
            "required": ["instance_id"],
        },
    },
    {
        "name": "query_dnac_device_health",
        "description": "Query DNAC live API for device health information. Use ONLY when MongoDB does not have the answer or the user explicitly asks to check DNAC live.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_name": {"type": "string", "description": "The device name"},
                "device_id": {"type": "string", "description": "The DNAC device UUID"},
            },
        },
    },
    {
        "name": "generate_visualization",
        "description": "Generate a chart visualization from data. Call this ONLY when you have determined the user wants a VISUALIZATION (not for AMBIGUOUS intent). Supply the chart_type, title, data array, and axis keys. For multi-series line/area/bar charts, provide multi_series_keys.",
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "pie", "area"],
                    "description": "The type of chart to render",
                },
                "title": {"type": "string", "description": "Chart title"},
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of data objects for the chart. Each object has keys matching x_key and y_key (or multi_series_keys).",
                },
                "x_key": {"type": "string", "description": "Key in data objects for the X axis / labels (default: 'label')"},
                "y_key": {"type": "string", "description": "Key in data objects for the Y axis values (default: 'value'). Ignored if multi_series_keys is set."},
                "colors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional array of hex color strings for the chart series",
                },
                "multi_series_keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "For multi-series charts, the keys in each data object that represent different series (e.g. ['Backdated', 'Auto Resolving', 'Non-Auto Resolving'])",
                },
            },
            "required": ["chart_type", "title", "data"],
        },
    },
]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an AI assistant for the DNAC Ops Center — a network operations dashboard that monitors Cisco DNA Center alerts. You help network engineers understand alert data, device status, and suppression metrics.

## DATA SOURCES
You have access to these tools:
1. **MongoDB tools** (query_alerts, get_device_status, get_device_history, get_kpi_summary) — contain historical alert data, classification results, and ServiceNow ticket info. ALWAYS try these first.
2. **DNAC live API tools** (query_dnac_issue, query_dnac_device_health) — live queries to Cisco DNA Center. Use ONLY when MongoDB doesn't have the answer OR the user explicitly asks to "check DNAC" or wants "live" / "current" status from DNAC.
3. **generate_visualization** — creates chart specs for the frontend to render.

## INTENT ANALYSIS RULES
Before calling any data tools, classify the user's intent:

**TEXT_ONLY** — user clearly wants a factual text answer:
- "What is...", "How many...", "Is there...", "Tell me about..."
- "What's the status of...", "Check if...", "List all..."
- Questions asking for a specific value, status, or yes/no answer

**VISUALIZATION** — user explicitly wants a chart/graph:
- "Show me a chart of...", "Plot...", "Visualize...", "Graph..."
- "Draw a bar chart...", "Create a pie chart...", "Show the trend..."
- Explicitly mentions a chart type (bar, line, pie, area)

**AMBIGUOUS** — could be either (ASK FOR CLARIFICATION):
- "Show me alerts by severity" — could be a table or a chart
- "Give me the breakdown of..." — could be text or pie chart
- "Show me device performance" — text summary or chart?
- "Compare X vs Y" — text comparison or chart?
- "What does the trend look like?" — text description or chart?

When intent is AMBIGUOUS:
- Do NOT call any data tools yet
- Respond with a clarification question, e.g.: "I can show this as a text summary with the numbers, or as a visual chart (bar/pie/line). Which would you prefer?"
- Wait for the user's clarification before proceeding

## RESPONSE RULES
1. **Be concise** — network engineers want facts, not fluff.
2. **Cite every data point** — at the end of your response, include a "Sources" section listing each tool you called and the query/parameters used.
3. **Never fabricate data** — if no results found, say so clearly.
4. **Format numbers** — use commas for thousands, percentages with 1 decimal.
5. **Timestamps** — convert epoch ms to human-readable UTC dates.
6. **Charts** — when generating a visualization, also include a brief text summary of what the chart shows.
7. **Colors** — use these colors for chart series: #2563eb (blue), #059669 (green), #dc2626 (red), #d97706 (amber), #7c3aed (purple), #0891b2 (cyan), #ea580c (orange).
"""


# ---------------------------------------------------------------------------
# ChatAgent — LangChain ChatOpenAI → Gemini
# ---------------------------------------------------------------------------
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)


def _build_langchain_tools() -> list:
    """Convert GEMINI_TOOL_DECLARATIONS to LangChain-style JSON tool schemas."""
    lc_tools = []
    for decl in GEMINI_TOOL_DECLARATIONS:
        lc_tools.append({
            "type": "function",
            "function": {
                "name": decl["name"],
                "description": decl["description"],
                "parameters": decl.get("parameters", {"type": "object", "properties": {}}),
            },
        })
    return lc_tools


class ChatAgent:
    """Gemini-powered agent using LangChain ChatOpenAI."""

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured. Update your .env file.")

        # LiteLLM gateway — already OpenAI-compatible
        base_url = GEMINI_BASE_URL.rstrip('/')

        self.llm = ChatOpenAI(
            model=GEMINI_MODEL,
            api_key=GEMINI_API_KEY,
            base_url=base_url,
            temperature=0.2,
            max_tokens=4096,
        )

        self.tools_schema = _build_langchain_tools()
        self.max_tool_rounds = 5

    def run(
        self,
        user_message: str,
        history: List[dict] = None,
        on_task: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """
        Run the agent loop.

        Returns:
            {
                "text": str,               # final answer
                "citations": [...],        # list of {tool, args, summary}
                "charts": [...],           # list of chart specs (may be empty)
                "clarification": str|None, # set if intent was ambiguous
                "suggestions": [...]|None, # quick-reply chips for clarification
            }
        """
        if on_task:
            on_task("Analyzing intent...")

        # Build LangChain message history
        messages = self._build_messages(user_message, history)
        citations: List[dict] = []
        charts: List[dict] = []

        # Bind tools to the model
        llm_with_tools = self.llm.bind_tools(self.tools_schema)

        for _round in range(self.max_tool_rounds):
            try:
                response: AIMessage = llm_with_tools.invoke(messages)
            except Exception as e:
                err_msg = str(e)
                if GEMINI_API_KEY:
                    err_msg = err_msg.replace(GEMINI_API_KEY, "[REDACTED]")
                logger.error(f"LLM call failed: {err_msg}")
                return {
                    "text": f"Sorry, I encountered an error: {err_msg}",
                    "citations": citations,
                    "charts": charts,
                    "clarification": None,
                    "suggestions": None,
                }

            # Check if there are tool calls
            tool_calls = response.tool_calls if hasattr(response, "tool_calls") else []

            if not tool_calls:
                # Final text answer
                final_text = response.content or ""
                messages.append(response)

                is_clarification = self._is_clarification(final_text)
                if is_clarification:
                    return {
                        "text": final_text,
                        "citations": citations,
                        "charts": charts,
                        "clarification": final_text,
                        "suggestions": self._extract_suggestions(final_text),
                    }

                return {
                    "text": final_text,
                    "citations": citations,
                    "charts": charts,
                    "clarification": None,
                    "suggestions": None,
                }

            # Process tool calls
            messages.append(response)

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("args", {})
                tool_call_id = tc.get("id", tool_name)

                label = TOOL_TASK_LABELS.get(tool_name, f"Running {tool_name}...")
                if on_task:
                    on_task(label)

                logger.info(f"Tool call: {tool_name}({json.dumps(tool_args, default=str)[:500]})")

                tool_fn = TOOLS.get(tool_name)
                if tool_fn is None:
                    result = {"error": f"Unknown tool: {tool_name}"}
                else:
                    try:
                        result = tool_fn(tool_args)
                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {e}")
                        result = {"error": str(e)}

                # Track citations
                citations.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "summary": self._summarize_result(tool_name, result),
                })

                # Track chart specs
                if tool_name == "generate_visualization" and "error" not in result:
                    charts.append(result)

                # Truncate large results
                result_str = json.dumps(result, default=str)
                if len(result_str) > 15000:
                    result_str = result_str[:15000] + '..."}'

                messages.append(
                    ToolMessage(
                        content=result_str,
                        tool_call_id=tool_call_id,
                    )
                )

        # Max rounds exceeded
        return {
            "text": "I reached the maximum number of tool calls. Here's what I found so far based on the data collected.",
            "citations": citations,
            "charts": charts,
            "clarification": None,
            "suggestions": None,
        }

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def _build_messages(self, user_message: str, history: list = None) -> list:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        if history:
            for msg in history[-10:]:
                role = msg.get("role", "user")
                text = msg.get("text", "")
                if role == "user":
                    messages.append(HumanMessage(content=text))
                else:
                    messages.append(AIMessage(content=text))

        messages.append(HumanMessage(content=user_message))
        return messages

    def _is_clarification(self, text: str) -> bool:
        """Heuristic: detect if the model is asking for clarification."""
        clarification_signals = [
            "which would you prefer",
            "would you like me to show",
            "would you prefer",
            "text summary or",
            "a visual chart",
            "bar chart or",
            "pie chart or",
            "text or a chart",
            "text summary with the numbers",
            "how would you like",
            "shall i show",
            "do you want a chart",
            "do you want me to",
            "would you like a",
        ]
        lower = text.lower()
        return any(signal in lower for signal in clarification_signals)

    def _extract_suggestions(self, text: str) -> list:
        """Extract quick-reply suggestions from a clarification response."""
        suggestions = []
        lower = text.lower()

        if "bar" in lower:
            suggestions.append("Bar chart")
        if "pie" in lower:
            suggestions.append("Pie chart")
        if "line" in lower or "trend" in lower:
            suggestions.append("Line chart")
        if "area" in lower:
            suggestions.append("Area chart")
        if "text" in lower or "summary" in lower or "numbers" in lower:
            suggestions.append("Text summary")

        if not suggestions:
            suggestions = ["Text summary", "Bar chart", "Pie chart"]
        elif "Text summary" not in suggestions:
            suggestions.insert(0, "Text summary")

        return suggestions

    def _summarize_result(self, tool_name: str, result: dict) -> str:
        """One-line summary for citations."""
        if "error" in result:
            return f"Error: {result['error']}"

        if tool_name == "query_alerts":
            return f"Found {result.get('count', 0)} alerts (query: {result.get('query_used', '{}')})"
        elif tool_name == "get_device_status":
            if result.get("found"):
                return f"Device '{result.get('device_name')}': {result.get('total_alerts', 0)} total alerts"
            return f"Device '{result.get('device_name')}' not found"
        elif tool_name == "get_device_history":
            return f"{result.get('count', 0)} historical alerts for '{result.get('device_name')}'"
        elif tool_name == "get_kpi_summary":
            return f"KPI summary: {result.get('total_alerts', 0)} total alerts, {result.get('suppression_rate', 0)}% suppression rate"
        elif tool_name == "query_dnac_issue":
            return f"DNAC issue {result.get('instance_id', '?')}: status={result.get('status', '?')}"
        elif tool_name == "query_dnac_device_health":
            return f"DNAC device health data retrieved"
        elif tool_name == "generate_visualization":
            return f"Generated {result.get('chart_type', '?')} chart: {result.get('title', '?')}"
        return f"{tool_name} completed"
