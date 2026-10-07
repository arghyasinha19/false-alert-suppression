"""
Tests for live device reachability cross-referencing in alert status verification (DNAC-03).
Covers:
- workflow/tools/dnac_status.py: check_alert_status reachability cross-referencing
- workflow/delayed.py: delayed check escalation for unreachable devices
"""
import os
import sys
from unittest.mock import MagicMock, patch
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from workflow.tools.dnac_status import check_alert_status, ACTIVE, RESOLVED, UNCERTAIN
from workflow.delayed import run_delayed_check


def make_mock_client(
    issue_status=None,
    active_issues=None,
    resolved_issues=None,
    reachable=True,
    reachability_status="Reachable",
    communication_state="REACHABLE",
    failure_reason=None,
    error_code=None,
    health_raises=False,
):
    client = MagicMock()
    client.get_issue_status.return_value = issue_status or "NOT_FOUND"

    def _get_issues(device_id=None, issue_status=None, **_):
        if issue_status == "ACTIVE":
            return active_issues or []
        if issue_status in ("RESOLVED", "IGNORED"):
            return resolved_issues or []
        return []

    client.get_device_issues.side_effect = _get_issues

    if health_raises:
        client.get_device_health.side_effect = RuntimeError("DNAC health API error")
    else:
        health_data = {
            "reachable": reachable,
            "health_score": 10 if reachable else -2,
            "raw_response": {
                "device_detail": {
                    "communicationState": communication_state,
                    "nwDeviceRole": "BORDER ROUTER",
                    "overallHealth": 10 if reachable else -2,
                },
                "network_device": {
                    "reachabilityStatus": reachability_status,
                    "reachabilityFailureReason": failure_reason,
                    "errorCode": error_code,
                },
            },
        }
        client.get_device_health.return_value = health_data

    return client


def test_unreachable_device_returns_active_when_assurance_issues_empty():
    """DNAC-03: When Assurance issues list is empty, an unreachable device returns ACTIVE."""
    client = make_mock_client(
        reachable=False,
        reachability_status="Unreachable",
        communication_state="UNREACHABLE",
        failure_reason="SNMP Connectivity Failed",
        error_code="DEV-UNREACHED",
    )

    status = check_alert_status(
        device_id="59db4c3b-874e-424c-a7fa-10746577486c",
        device_name="tr-ist-rtr01",
        issue_name="Network Device 10.254.0.93 is unreachable",
        client=client,
    )

    assert status == ACTIVE
    client.get_device_health.assert_called_once_with("59db4c3b-874e-424c-a7fa-10746577486c")


def test_snmp_timeout_failure_reason_returns_active():
    """DNAC-03: Device with SNMP failure reason NCIM12013 returns ACTIVE."""
    client = make_mock_client(
        reachable=False,
        reachability_status="Unreachable",
        communication_state="UNREACHABLE",
        failure_reason="NCIM12013: SNMP request timeout",
    )

    status = check_alert_status(
        device_id="dev-uuid-snmp",
        device_name="tr-ist-rtr01",
        issue_name="SNMP connectivity timeout on controller link",
        client=client,
    )

    assert status == ACTIVE


def test_unreachable_device_with_any_alert_returns_active():
    """DNAC-03: Any alert on an explicitly unreachable node is acknowledged as ACTIVE."""
    client = make_mock_client(
        reachable=False,
        reachability_status="Unreachable",
        communication_state="UNREACHABLE",
    )

    status = check_alert_status(
        device_id="dev-uuid-1",
        device_name="edge-sw01",
        issue_name="Interface GigabitEthernet1/0/1 down",
        client=client,
    )

    assert status == ACTIVE


def test_reachable_device_with_cleared_reachability_alert_returns_resolved():
    """DNAC-03: When device is reachable and no active issues exist, reachability alert resolves."""
    client = make_mock_client(
        reachable=True,
        reachability_status="Reachable",
        communication_state="REACHABLE",
    )

    status = check_alert_status(
        device_id="dev-uuid-restored",
        device_name="tr-ist-rtr01",
        issue_name="Network Device 10.254.0.93 is unreachable",
        client=client,
    )

    assert status == RESOLVED


def test_reachable_device_with_unmatched_domain_alert_returns_uncertain():
    """DNAC-03: Non-reachability alerts (e.g. BGP) with no match return UNCERTAIN to escalate."""
    client = make_mock_client(
        reachable=True,
        reachability_status="Reachable",
        communication_state="REACHABLE",
    )

    status = check_alert_status(
        device_id="dev-uuid-bgp",
        device_name="core-rtr01",
        issue_name="BGP peer 192.168.1.1 down",
        client=client,
    )

    assert status == UNCERTAIN


def test_missing_device_id_resolved_via_device_name():
    """DNAC-03: When device_id is missing, it is auto-resolved via hostname/IP before checking."""
    client = make_mock_client(
        reachable=False,
        reachability_status="Unreachable",
        communication_state="UNREACHABLE",
        failure_reason="SNMP Connectivity Failed",
    )
    client.get_device_by_name_or_ip.return_value = [{
        "device_id": "auto-resolved-uuid-99",
        "device_name": "tr-ist-rtr01",
        "ip_address": "10.254.0.93",
        "reachable": False,
    }]

    status = check_alert_status(
        device_id=None,
        device_name="10.254.0.93",
        issue_name="Device unreachable",
        client=client,
    )

    assert status == ACTIVE
    client.get_device_by_name_or_ip.assert_called_once_with("10.254.0.93")
    client.get_device_health.assert_called_once_with("auto-resolved-uuid-99")


def test_health_check_exception_gracefully_returns_uncertain():
    """DNAC-03: If health check raises an exception, return UNCERTAIN without raising."""
    client = make_mock_client(health_raises=True)

    status = check_alert_status(
        device_id="dev-err",
        device_name="rtr01",
        issue_name="Device unreachable",
        client=client,
    )

    assert status == UNCERTAIN


def test_delayed_check_escalates_unreachable_device_as_non_auto_resolving():
    """DNAC-03: Delayed check pipeline marks unreachable device as Non-Auto Resolving and escalates."""
    alert = {
        "event_id": "EVT-9001",
        "device_id": "59db4c3b-874e-424c-a7fa-10746577486c",
        "device_name": "tr-ist-rtr01",
        "issue_name": "Network Device 10.254.0.93 is unreachable",
    }

    mock_snow = MagicMock()
    mock_snow.create_incident.return_value = {"sys_id": "INC009001", "number": "INC009001"}

    with patch("workflow.delayed.check_alert_status", return_value=ACTIVE), \
         patch("workflow.nodes.node_agent_4_servicenow.ServiceNowClient", return_value=mock_snow), \
         patch("workflow.nodes.node_email_notifier.email_notifier", return_value=None):
        state = run_delayed_check(alert)

    assert state["results"]["delayed_check"]["data"]["dnac_status"] == ACTIVE
    assert state["results"]["agent_2"]["data"]["predicted_category"] == "Non-Auto Resolving"
    assert "delayed_check: DNAC status ACTIVE" in state["results"]["agent_2"]["reason"]
