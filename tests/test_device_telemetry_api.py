"""
Unit and API integration tests for device telemetry and live-poll endpoints:
- GET  /api/devices/{device_name}/telemetry
- GET  /api/device/{device_name}/telemetry
- POST /api/devices/{device_name}/live-poll
- POST /api/device/{device_name}/live-poll
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from dashboard.api import app
from app.exceptions import DeviceNotFoundError, DNACConnectionError

client = TestClient(app)

MOCK_DEVICE_INFO = {
    "device_name": "cat9300-access-01",
    "ip_address": "10.48.200.10",
    "model": "C9300-48P",
    "os_version": "17.9.4a",
    "serial": "FOC12345678",
    "mac": "00:11:22:33:44:55",
    "reachable": True,
    "device_id": "11111111-2222-3333-4444-555555555555",
}

MOCK_HEALTH_VITALS = {
    "cpu": 18.5,
    "memory": 44.2,
    "packet_drop": 0.0,
    "health_score": 10,
    "interface_error_count": 0,
    "poe_status": "NORMAL",
    "uptime_seconds": 987654,
    "reachable": True,
    "raw_response": {"status": "ok"},
}


def test_get_telemetry_live_success():
    """Verify GET /api/devices/{name}/telemetry returns 200 with source: 'dnac_live'."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.return_value = [MOCK_DEVICE_INFO]
    mock_dnac.get_device_health.return_value = MOCK_HEALTH_VITALS

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac):
        res = client.get("/api/devices/cat9300-access-01/telemetry")

    assert res.status_code == 200
    data = res.json()
    assert data["device_name"] == "cat9300-access-01"
    assert data["device_id"] == "11111111-2222-3333-4444-555555555555"
    assert data["source"] == "dnac_live"
    assert data["telemetry"]["cpu"] == 18.5
    assert data["telemetry"]["memory"] == 44.2
    assert data["telemetry"]["health_score"] == 10
    assert data["telemetry"]["reachable"] is True
    assert data["device_info"]["model"] == "C9300-48P"
    assert data["device_info"]["serial"] == "FOC12345678"


def test_get_telemetry_singular_route_alias():
    """Verify GET /api/device/{name}/telemetry acts as an identical route alias."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.return_value = [MOCK_DEVICE_INFO]
    mock_dnac.get_device_health.return_value = MOCK_HEALTH_VITALS

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac):
        res = client.get("/api/device/cat9300-access-01/telemetry")

    assert res.status_code == 200
    data = res.json()
    assert data["device_name"] == "cat9300-access-01"
    assert data["source"] == "dnac_live"
    assert data["telemetry"]["cpu"] == 18.5


def test_get_telemetry_offline_with_cached_state():
    """Verify fallback to MongoDB cache with source: 'cached_offline' when DNAC is down."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.side_effect = DNACConnectionError("DNAC appliance unreachable")

    # Mock mongo collection device_telemetry
    mock_mongo = MagicMock()
    mock_coll = MagicMock()
    mock_coll.find_one.return_value = {
        "device_name": "cat9300-access-01",
        "device_id": "11111111-2222-3333-4444-555555555555",
        "last_updated": "2026-10-05T07:00:00Z",
        "telemetry": {
            "cpu": 15.0,
            "memory": 40.0,
            "packet_drop": 0.0,
            "health_score": 9,
            "interface_error_count": 1,
            "poe_status": "NORMAL",
            "uptime_seconds": 900000,
            "reachable": True,
        },
        "device_info": MOCK_DEVICE_INFO,
    }
    mock_mongo.get_collection.return_value = mock_coll

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac), \
         patch("dashboard.api.mongo", mock_mongo):
        res = client.get("/api/devices/cat9300-access-01/telemetry")

    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "cached_offline"
    assert data["telemetry"]["cpu"] == 15.0
    assert data["telemetry"]["reachable"] is False
    assert data["device_info"]["model"] == "C9300-48P"


def test_get_telemetry_offline_without_cache():
    """Verify total fallback to null vitals and source: 'offline' when no cache exists."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.side_effect = DNACConnectionError("Network timeout")

    mock_mongo = MagicMock()
    mock_coll = MagicMock()
    mock_coll.find_one.return_value = None
    mock_mongo.get_collection.return_value = mock_coll

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac), \
         patch("dashboard.api.mongo", mock_mongo):
        res = client.get("/api/devices/unseen-switch-99/telemetry")

    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "offline"
    assert data["telemetry"]["cpu"] is None
    assert data["telemetry"]["memory"] is None
    assert data["telemetry"]["reachable"] is False


def test_get_telemetry_device_not_found():
    """Verify handling when DNAC raises DeviceNotFoundError."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.side_effect = DeviceNotFoundError("missing-device")

    mock_mongo = MagicMock()
    mock_coll = MagicMock()
    mock_coll.find_one.return_value = None
    mock_mongo.get_collection.return_value = mock_coll

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac), \
         patch("dashboard.api.mongo", mock_mongo):
        res = client.get("/api/devices/missing-device/telemetry")

    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "offline"
    assert data["telemetry"]["reachable"] is False


def test_post_live_poll_success():
    """Verify POST /api/devices/{name}/live-poll updates alerts and returns consolidated state."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.return_value = [MOCK_DEVICE_INFO]
    mock_dnac.get_device_health.return_value = MOCK_HEALTH_VITALS

    mock_mongo = MagicMock()
    mock_alerts_coll = MagicMock()
    # 2 active alerts found for this device
    mock_alerts_coll.find.return_value = [
        {"_id": "id1", "alert_details": {"event_id": "EVT-101", "device_name": "cat9300-access-01"}},
        {"_id": "id2", "alert_details": {"event_id": "EVT-102", "device_name": "cat9300-access-01"}},
    ]
    mock_telemetry_coll = MagicMock()

    def get_collection(name):
        if name == "alert_results":
            return mock_alerts_coll
        elif name == "device_telemetry":
            return mock_telemetry_coll
        return None

    mock_mongo.get_collection.side_effect = get_collection

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac), \
         patch("dashboard.api.mongo", mock_mongo), \
         patch("dashboard.dnac_monitor.check_dashboard_dnac_status", return_value="RESOLVED"):
        res = client.post("/api/devices/cat9300-access-01/live-poll")

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["dnac_reachable"] is True
    assert data["alerts_updated"] == 2
    assert data["telemetry"]["cpu"] == 18.5
    assert data["source"] == "dnac_live"
    # Ensure update_one was called twice for the alerts
    assert mock_alerts_coll.update_one.call_count == 2


def test_post_live_poll_singular_alias():
    """Verify POST /api/device/{name}/live-poll route alias works identically."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.return_value = [MOCK_DEVICE_INFO]
    mock_dnac.get_device_health.return_value = MOCK_HEALTH_VITALS

    mock_mongo = MagicMock()
    mock_coll = MagicMock()
    mock_coll.find.return_value = []
    mock_mongo.get_collection.return_value = mock_coll

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac), \
         patch("dashboard.api.mongo", mock_mongo):
        res = client.post("/api/device/cat9300-access-01/live-poll")

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["dnac_reachable"] is True


def test_post_live_poll_dnac_offline_graceful():
    """Verify live-poll returns warning without raising 500 when DNAC is offline."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.side_effect = DNACConnectionError("DNAC connection refused")

    mock_mongo = MagicMock()
    mock_coll = MagicMock()
    mock_coll.find.return_value = []
    mock_coll.find_one.return_value = None
    mock_mongo.get_collection.return_value = mock_coll

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac), \
         patch("dashboard.api.mongo", mock_mongo):
        res = client.post("/api/devices/cat9300-access-01/live-poll")

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "warning"
    assert data["dnac_reachable"] is False
    assert data["telemetry"]["reachable"] is False
