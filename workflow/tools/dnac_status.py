"""
Single source of truth for "is this DNAC alert still active?".

Used by:
  - workflow/api.py            (/api/v1/invoke/delayed)
  - workflow/run_delayed.py    (CLI equivalent)
  - dashboard/dnac_monitor.py  (background dashboard sync)

Returns one of: "ACTIVE", "RESOLVED", "UNCERTAIN".

Lookup order
------------
1. By Assurance **issueId** (extracted from the webhook's ciscoDnaEventLink)
   via GET /dna/data/api/v1/assuranceIssues/{id}.
2. Device-scoped scan: GET /dna/intent/api/v1/issues?deviceId=<uuid>&issueStatus=...
   matching by issueId first, then by issue name **on that device only**.
3. Anything else -> UNCERTAIN (callers escalate to ServiceNow).

Any DNAC error results in UNCERTAIN, never RESOLVED, so a DNAC outage cannot
cause a genuine alert to be suppressed.
"""
import logging
import os
import re
import sys
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

ACTIVE = "ACTIVE"
RESOLVED = "RESOLVED"
UNCERTAIN = "UNCERTAIN"

_CLOSED = {"RESOLVED", "IGNORED", "CLEARED", "DELETED", "INACTIVE"}

_REACHABILITY_KEYWORDS = (
    "unreachable",
    "reachability",
    "connectivity",
    "connection timeout",
    "ping",
    "offline",
    "disconnect",
    "dev-unreached",
    "ncim12013",
    "device down",
    "node down",
)


def _is_reachability_alert(issue_name: Optional[str]) -> bool:
    """Return True if the alert name relates to device reachability or connectivity."""
    target = _norm(issue_name)
    return any(kw in target for kw in _REACHABILITY_KEYWORDS)


def load_dnac_client():
    """Build a DNACClient from config.yaml (raises on misconfiguration)."""
    from app.dnac_client import DNACClient

    with open(os.path.join(PROJECT_ROOT, "config.yaml"), "r") as f:
        config = yaml.safe_load(f) or {}
    return DNACClient(config.get("dnac", {}))


def _norm(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _issue_matches(issue: dict, issue_id: Optional[str], issue_name: Optional[str]) -> bool:
    """Match a DNAC issue (already filtered to the right device)."""
    if issue_id and str(issue.get("issueId") or issue.get("id") or "") == str(issue_id):
        return True
    target = _norm(issue_name)
    if not target:
        return False
    candidate = _norm(issue.get("name") or issue.get("issueName") or issue.get("title"))
    if not candidate:
        return False
    # Exact, or one fully contains the other (DNAC sometimes appends the device
    # name to the issue title). Safe because the list is scoped to one device.
    return candidate == target or target in candidate or candidate in target


def check_alert_status(
    issue_id: Optional[str] = None,
    device_id: Optional[str] = None,
    device_name: Optional[str] = None,
    issue_name: Optional[str] = None,
    client=None,
    **_ignored,
) -> str:
    """Return ACTIVE / RESOLVED / UNCERTAIN for one alert. Never raises."""
    try:
        client = client or load_dnac_client()
    except Exception as exc:
        logger.error(f"Cannot initialise DNAC client: {exc}. Returning UNCERTAIN.")
        return UNCERTAIN

    # 1. Primary: by issueId
    if issue_id:
        try:
            status = client.get_issue_status(issue_id)
            logger.info(f"DNAC primary check issue_id={issue_id}: {status}")
            if status == "ACTIVE":
                return ACTIVE
            if status in _CLOSED:
                return RESOLVED
            # NOT_FOUND / UNSUPPORTED / UNKNOWN -> fall through to device scan
        except Exception as exc:
            logger.warning(f"DNAC primary check failed for issue_id={issue_id}: {exc}. Trying device scan.")

    # 2. Device-scoped scan
    # If device_id is missing, attempt resolution by hostname / management IP
    if not device_id and device_name and hasattr(client, "get_device_by_name_or_ip"):
        try:
            found_devs = client.get_device_by_name_or_ip(device_name)
            if found_devs and isinstance(found_devs, list):
                resolved_id = found_devs[0].get("device_id")
                if resolved_id:
                    device_id = resolved_id
                    logger.info(f"Resolved device_id={device_id} from device_name={device_name}")
        except Exception as exc:
            logger.debug(f"Device name resolution failed for {device_name}: {exc}")

    if not device_id:
        logger.warning(
            f"No issue_id status and no device_id (device_name={device_name}); returning UNCERTAIN."
        )
        return UNCERTAIN

    if not issue_id and not issue_name:
        logger.warning("Neither issue_id nor issue_name available to match against; returning UNCERTAIN.")
        return UNCERTAIN

    try:
        for issue in client.get_device_issues(device_id=device_id, issue_status="ACTIVE"):
            if _issue_matches(issue, issue_id, issue_name):
                logger.info(f"Device scan: matching ACTIVE issue on device {device_id}")
                return ACTIVE

        for wanted in ("RESOLVED", "IGNORED"):
            for issue in client.get_device_issues(device_id=device_id, issue_status=wanted):
                if _issue_matches(issue, issue_id, issue_name):
                    logger.info(f"Device scan: matching {wanted} issue on device {device_id}")
                    return RESOLVED
    except Exception as exc:
        logger.error(f"DNAC device scan failed for device {device_id}: {exc}. Returning UNCERTAIN.")
        return UNCERTAIN

    # 3. Live reachability cross-referencing (DNAC-03)
    if hasattr(client, "get_device_health"):
        try:
            health = client.get_device_health(device_id)
            if isinstance(health, dict):
                is_reachable = health.get("reachable")
                raw = health.get("raw_response") if isinstance(health.get("raw_response"), dict) else {}
                raw_net = raw.get("network_device") if isinstance(raw.get("network_device"), dict) else {}
                raw_detail = raw.get("device_detail") if isinstance(raw.get("device_detail"), dict) else {}

                reach_status = str(raw_net.get("reachabilityStatus", "")).lower()
                comm_state = str(raw_detail.get("communicationState", "")).upper()
                fail_reason = raw_net.get("reachabilityFailureReason") or ""

                is_unreachable = (
                    is_reachable is False
                    or reach_status in ("unreachable", "false")
                    or comm_state in ("UNREACHABLE", "DISCONNECTED")
                    or bool(fail_reason)
                )

                if is_unreachable:
                    reason_desc = fail_reason or comm_state or reach_status or "Unreachable"
                    logger.info(
                        f"Live reachability check: device {device_id} is explicitly UNREACHABLE "
                        f"in DNAC ({reason_desc}). Acknowledging alert as ACTIVE."
                    )
                    return ACTIVE

                if is_reachable is True and _is_reachability_alert(issue_name):
                    logger.info(
                        f"Live reachability check: device {device_id} is REACHABLE with no active "
                        f"issues in DNAC for reachability alert '{issue_name}'. Returning RESOLVED."
                    )
                    return RESOLVED
        except Exception as exc:
            logger.warning(f"DNAC live reachability check failed for device {device_id}: {exc}")

    logger.warning(f"No matching issue found on device {device_id}/{device_name}; returning UNCERTAIN.")
    return UNCERTAIN

