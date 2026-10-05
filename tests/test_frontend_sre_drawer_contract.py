"""
Frontend SRE Drawer Contract & Integration Test
===============================================
Validates that:
1. NetworkOperations.jsx and App.jsx correctly wire the slide-out drawer
   to the live backend endpoints (/api/devices/{name}/telemetry and
   /api/devices/{name}/live-poll) with URI encoding and AbortController.
2. The artificial setTimeout polling in handlePollDNAC has been replaced.
3. App.jsx passes onRefresh to NetworkOperations for fleet-wide sync.
4. App.css includes all required provenance pill and banner styles.
5. Live backend endpoint payloads match the schema and keys expected
   by the frontend drawer vitals and inventory cards.
"""

import os
import sys
import re
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard.api import app

client = TestClient(app)

NETWORK_OPERATIONS_PATH = os.path.join(project_root, "dashboard", "src", "NetworkOperations.jsx")
APP_JSX_PATH = os.path.join(project_root, "dashboard", "src", "App.jsx")
APP_CSS_PATH = os.path.join(project_root, "dashboard", "src", "App.css")


def test_network_operations_wireup_source_contract():
    """Verify NetworkOperations.jsx has real endpoints and no mock setTimeout."""
    with open(NETWORK_OPERATIONS_PATH, "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Verify endpoint URLs are called with encodeURIComponent
    assert "/api/devices/${encodeURIComponent(" in src, "Missing URI-encoded endpoint call in NetworkOperations.jsx"
    assert "/telemetry" in src, "Missing /telemetry endpoint call in NetworkOperations.jsx"
    assert "/live-poll" in src, "Missing /live-poll endpoint call in NetworkOperations.jsx"

    # 2. Verify AbortController is used to prevent async race conditions
    assert "new AbortController()" in src, "AbortController must be instantiated for telemetry requests"
    assert "telemetryAbortRef" in src, "telemetryAbortRef must be defined to cancel in-flight requests"

    # 3. Verify handlePollDNAC does NOT use procedural setTimeout
    match_poll = re.search(r"const handlePollDNAC\s*=\s*async\s*\(\)\s*=>\s*{(.*?)\n\s*};", src, re.DOTALL)
    assert match_poll is not None, "handlePollDNAC must be an async function"
    poll_body = match_poll.group(1)
    assert "setTimeout" not in poll_body, "handlePollDNAC must not contain artificial setTimeout"
    assert "POST" in poll_body, "handlePollDNAC must issue an HTTP POST request"

    # 4. Verify onRefresh is called on successful poll
    assert "onRefresh" in poll_body, "handlePollDNAC must trigger onRefresh callback"

    # 5. Verify dynamic toast titles
    assert "DNAC Live Synchronized" in src
    assert "DNAC Controller Unreachable" in src
    assert "Assurance Polling Failed" in src


def test_app_jsx_passes_on_refresh_to_network_operations():
    """Verify App.jsx passes onRefresh callback to NetworkOperations."""
    with open(APP_JSX_PATH, "r", encoding="utf-8") as f:
        src = f.read()

    match_noc = re.search(r"<NetworkOperations\b([^>]*?)/?>", src, re.DOTALL)
    assert match_noc is not None, "NetworkOperations component not found in App.jsx"
    attrs = match_noc.group(1)
    assert "onRefresh={fetchData}" in attrs or "onRefresh" in attrs, (
        "App.jsx must pass onRefresh prop to NetworkOperations"
    )


def test_app_css_defines_provenance_and_banner_classes():
    """Verify App.css contains styling for provenance pills, banners, and loading dot."""
    with open(APP_CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()

    assert ".noc-provenance-pill" in css
    assert ".noc-provenance-pill.live" in css
    assert ".noc-provenance-pill.cached" in css
    assert ".noc-provenance-pill.offline" in css
    assert ".noc-provenance-banner" in css
    assert ".noc-provenance-banner.live" in css
    assert ".noc-provenance-banner.cached" in css
    assert ".noc-provenance-banner.offline" in css
    assert ".noc-loading-dot" in css
    assert ".noc-null-val" in css


def test_telemetry_endpoint_schema_contract():
    """Verify GET /api/devices/{name}/telemetry returns exact contract required by drawer."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.return_value = [{
        "device_name": "core-router-01",
        "device_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "ip_address": "10.10.10.1",
        "model": "Cisco ASR 9904 Core Router",
        "os_version": "IOS-XR 7.5.2",
        "serial": "FOC9904001",
        "mac": "00:2A:6A:11:22:33",
        "reachable": True,
    }]
    mock_dnac.get_device_health.return_value = {
        "cpu": 24,
        "memory": 48,
        "packet_drop": 0.01,
        "health_score": 95,
        "interface_error_count": 0,
        "poe_status": "580W / 740W (78%)",
        "uptime_seconds": 864000,
        "reachable": True,
        "raw_response": {},
    }

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac):
        res = client.get("/api/devices/core-router-01/telemetry")

    assert res.status_code == 200
    data = res.json()
    assert data["source"] in ("dnac_live", "cached_offline", "offline")
    assert "timestamp" in data
    assert "telemetry" in data
    assert "device_info" in data

    # Verify telemetry vitals keys expected by NetworkOperations.jsx
    tel = data["telemetry"]
    assert "cpu" in tel
    assert "memory" in tel
    assert "packet_drop" in tel
    assert "uptime_seconds" in tel
    assert "reachable" in tel

    # Verify device_info keys expected by NetworkOperations.jsx
    info = data["device_info"]
    assert "model" in info
    assert "os_version" in info
    assert "serial" in info
    assert "mac" in info
    assert "ip_address" in info


def test_live_poll_endpoint_schema_contract():
    """Verify POST /api/devices/{name}/live-poll returns exact contract required by handlePollDNAC."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.return_value = [{
        "device_name": "core-router-01",
        "device_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "ip_address": "10.10.10.1",
        "model": "Cisco ASR 9904 Core Router",
        "os_version": "IOS-XR 7.5.2",
        "serial": "FOC9904001",
        "mac": "00:2A:6A:11:22:33",
        "reachable": True,
    }]
    mock_dnac.get_device_health.return_value = {
        "cpu": 32,
        "memory": 52,
        "packet_drop": 0.0,
        "health_score": 98,
        "interface_error_count": 0,
        "poe_status": "340W / 740W (46%)",
        "uptime_seconds": 864500,
        "reachable": True,
        "raw_response": {},
    }

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac):
        res = client.post("/api/devices/core-router-01/live-poll")

    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("success", "warning")
    assert data["device_name"] == "core-router-01"
    assert "alerts_updated" in data
    assert "telemetry" in data
    assert "device_info" in data
    assert "timestamp" in data
