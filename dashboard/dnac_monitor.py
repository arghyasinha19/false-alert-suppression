"""
Dashboard DNAC Monitor
======================
Thin wrapper used by the dashboard's background sync. All DNAC status logic
lives in ``workflow/tools/dnac_status.py`` so the workflow, the delayed check
and the dashboard can never disagree.

This function **never raises**; it always returns ``ACTIVE``, ``RESOLVED`` or
``UNCERTAIN``.
"""

import os
import sys
import logging

dashboard_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(dashboard_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger("DashboardDNACMonitor")


def _load_dnac_client():
    """Create a DNACClient from config.yaml, or None on any error."""
    try:
        from workflow.tools.dnac_status import load_dnac_client
        return load_dnac_client()
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
    issue_id: str = None,
) -> str:
    """
    Return ACTIVE / RESOLVED / UNCERTAIN for an alert.

    ``instance_id`` is accepted for backwards compatibility but is NOT used as
    an issue identifier (it is the webhook notification instance, not the
    Assurance issueId).
    """
    client = _load_dnac_client()
    if client is None:
        return "UNCERTAIN"
    try:
        from workflow.tools.dnac_status import check_alert_status
        return check_alert_status(
            issue_id=issue_id,
            device_id=device_id,
            device_name=device_name,
            issue_name=issue_name,
            client=client,
        )
    except Exception as e:
        logger.warning(f"Dashboard DNAC check failed for device={device_id or device_name}: {e}")
        return "UNCERTAIN"
