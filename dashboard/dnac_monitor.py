"""
Dashboard DNAC Monitor
======================
A standalone, resilient DNAC status checking function designed exclusively
for the dashboard's background sync.  This is completely independent from
the workflow's ``check_dnac_status`` in ``workflow/run_delayed.py``.

Key difference: this function **never raises**.  It always returns a
status string (``ACTIVE``, ``RESOLVED``, or ``UNCERTAIN``) so the
dashboard can always display device data from MongoDB regardless of
DNAC connectivity.
"""

import os
import sys
import logging

# Ensure project root is importable
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(dashboard_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger("DashboardDNACMonitor")


def _load_dnac_client():
    """
    Create and return a DNACClient instance from config.yaml.
    Returns None if anything goes wrong (missing config, bad creds, etc.).
    """
    try:
        import yaml
        from app.dnac_client import DNACClient

        config_path = os.path.join(project_root, "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        dnac_config = config.get("dnac", {})
        return DNACClient(dnac_config)
    except Exception as e:
        logger.error(f"Failed to initialise DNAC client: {e}")
        return None


def check_dashboard_dnac_status(
    instance_id: str = None,
    device_id: str = None,
    device_name: str = None,
    issue_name: str = None,
    issue_details: str = None,
    event_id: str = None,
) -> str:
    """
    Check DNAC to determine whether an alert is still active.

    This is the **dashboard-only** variant.  Unlike the workflow's
    ``check_dnac_status`` it:
      * Never raises – always returns a status string.
      * Returns ``"ACTIVE"``, ``"RESOLVED"``, or ``"UNCERTAIN"``.

    Logic
    -----
    1. Primary check via ``instance_id``  (DNAC issue-by-id API).
    2. Fallback A – scan the device's *active* issues for a text match.
    3. Fallback B – scan the device's *resolved* issues for a text match.
    4. If nothing matched → ``"UNCERTAIN"``.
    """
    client = _load_dnac_client()
    if client is None:
        return "UNCERTAIN"

    # ── 1. Primary check using instance_id ──────────────────────────
    if instance_id:
        try:
            status = client.get_issue_status(instance_id)
            logger.info(
                f"Dashboard DNAC check – instance_id={instance_id}: status={status}"
            )
            if status != "NOT_FOUND":
                if status.upper() in ("RESOLVED", "IGNORED", "CLEARED", "DELETED"):
                    return "RESOLVED"
                else:
                    return "ACTIVE"
            logger.info(
                f"instance_id={instance_id} NOT_FOUND. Falling back to device scan."
            )
        except Exception as e:
            logger.warning(
                f"Dashboard DNAC primary check failed for instance_id={instance_id}: {e}. "
                f"Falling back to device scan."
            )

    # ── Helper: fuzzy text match against issue fields ───────────────
    def _is_match(issue: dict) -> bool:
        target_texts = [
            str(t).strip().lower()
            for t in (issue_name, issue_details, event_id)
            if t
        ]
        if not target_texts:
            return False
        issue_texts = [
            str(issue.get(k, "")).strip().lower()
            for k in (
                "name", "issueName", "description", "issueDescription",
                "issueDetails", "title", "summary", "eventId",
            )
            if issue.get(k)
        ]
        for target in target_texts:
            for itext in issue_texts:
                if target in itext or itext in target:
                    return True
        return False

    # ── 2. Fallback A – active issues on device ────────────────────
    try:
        active_issues = client.get_device_issues(
            device_id=device_id,
            device_name=device_name,
            issue_status="ACTIVE",
        )
        for issue in active_issues:
            iss_status = str(
                issue.get("issueStatus", issue.get("status", "ACTIVE"))
            ).upper()
            if iss_status not in ("RESOLVED", "IGNORED", "CLEARED", "DELETED"):
                if _is_match(issue):
                    logger.info(
                        f"Dashboard fallback: matched ACTIVE issue on "
                        f"device={device_id or device_name}"
                    )
                    return "ACTIVE"
    except Exception as e:
        logger.warning(
            f"Dashboard DNAC fallback-A (active scan) failed for "
            f"device={device_id or device_name}: {e}"
        )

    # ── 3. Fallback B – resolved issues on device ──────────────────
    try:
        resolved_issues = client.get_device_issues(
            device_id=device_id,
            device_name=device_name,
            issue_status="RESOLVED",
        )
        for issue in resolved_issues:
            iss_status = str(
                issue.get("issueStatus", issue.get("status", "RESOLVED"))
            ).upper()
            if iss_status in ("RESOLVED", "IGNORED", "CLEARED", "DELETED"):
                if _is_match(issue):
                    logger.info(
                        f"Dashboard fallback: matched RESOLVED issue on "
                        f"device={device_id or device_name}"
                    )
                    return "RESOLVED"
    except Exception as e:
        logger.warning(
            f"Dashboard DNAC fallback-B (resolved scan) failed for "
            f"device={device_id or device_name}: {e}"
        )

    # ── 4. Not found anywhere ──────────────────────────────────────
    logger.info(
        f"Dashboard DNAC: no match found for device={device_id or device_name}. "
        f"Returning UNCERTAIN."
    )
    return "UNCERTAIN"
