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


def test_telemetry_raw_response_hardware_extraction():
    """Verify hardware specs (model, serial, mac, os_version, ip) are extracted from raw_response."""
    mock_dnac = MagicMock()
    # Simulate inventory lookup returning only UUID without detailed device_info
    mock_dnac.get_device_by_name_or_ip.return_value = [{
        "device_id": "59db4c3b-874e-424c-a7fa-10746577486c",
        "device_name": "tr-ist-rtr01",
        "model": "Unknown",
        "serial": "Unknown",
        "mac": "Unknown",
        "os_version": "Unknown",
        "ip_address": "Unknown",
        "reachable": False,
    }]

    # Real production raw_response structure from captured DNAC response
    production_raw_response = {
        "device_detail": {
            "overallHealth": -2,
            "managementIpAddr": "10.254.0.93",
            "communicationState": "UNREACHABLE",
            "nwDeviceRole": "BORDER ROUTER",
            "osType": "IOS-XE",
            "nwDeviceType": "Cisco 4331 Integrated Services Router",
            "platformId": "ISR4331/K9",
            "serialNumber": "FDO2517M1EG",
            "macAddress": "6C:13:D5:BE:91:F0",
            "softwareVersion": "17.12.8",
            "nwDeviceName": "tr-ist-rtr01",
            "location": "Global/EMEA/TR Istanbul/Umut Street",
        },
        "network_device": {
            "family": "Routers",
            "softwareVersion": "17.12.8",
            "macAddress": "6c:13:d5:be:91:f0",
            "serialNumber": "FDO2517M1EG",
            "managementIpAddress": "10.254.0.93",
            "platformId": "ISR4331/K9",
            "type": "Cisco 4331 Integrated Services Router",
            "hostname": "tr-ist-rtr01",
            "reachabilityStatus": "Unreachable",
            "reachabilityFailureReason": "SNMP Connectivity Failed",
            "errorCode": "DEV-UNREACHED",
        }
    }

    mock_health = {
        "cpu": None,
        "memory": None,
        "packet_drop": None,
        "health_score": -2,
        "interface_error_count": None,
        "poe_status": "UNKNOWN",
        "uptime_seconds": 692019,
        "reachable": False,
        "raw_response": production_raw_response,
    }
    mock_dnac.get_device_health.return_value = mock_health

    mock_mongo = MagicMock()
    mock_coll = MagicMock()
    mock_coll.find_one.return_value = None
    mock_mongo.get_collection.return_value = mock_coll

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac), \
         patch("dashboard.api.mongo", mock_mongo):
        res = client.get("/api/devices/10.254.0.93/telemetry")

    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "dnac_live"
    info = data["device_info"]
    assert info["model"] == "Cisco 4331 Integrated Services Router"
    assert info["serial"] == "FDO2517M1EG"
    assert info["mac"] in ("6c:13:d5:be:91:f0", "6C:13:D5:BE:91:F0")
    assert info["os_version"] == "17.12.8"
    assert info["ip_address"] == "10.254.0.93"
    assert info.get("hostname") == "tr-ist-rtr01"

    # Verify MongoDB cache was updated with the extracted specs
    assert mock_coll.update_one.called
    upsert_call = mock_coll.update_one.call_args[0]
    set_doc = upsert_call[1]["$set"]
    assert set_doc["device_info"]["model"] == "Cisco 4331 Integrated Services Router"
    assert set_doc["device_info"]["serial"] == "FDO2517M1EG"


def test_extract_site_from_location_path():
    """DNAC-05: Verify site name extraction strips country prefixes from hierarchy paths."""
    from dashboard.device_service import extract_site_from_location_path

    assert extract_site_from_location_path("Global/EMEA/TR Istanbul/Umut Street") == "Istanbul"
    assert extract_site_from_location_path("Global/AMER/US New York/Building 4") == "New York"
    assert extract_site_from_location_path("Global/APAC/London") == "London"
    assert extract_site_from_location_path(None) is None


def test_telemetry_diagnostics_and_site_extraction():
    """DNAC-04 & DNAC-05: Verify diagnostics and site identity extraction from raw response."""
    mock_dnac = MagicMock()
    mock_dnac.get_device_by_name_or_ip.return_value = [{
        "device_id": "59db4c3b-874e-424c-a7fa-10746577486c",
        "device_name": "tr-ist-rtr01",
        "model": "Unknown",
        "serial": "Unknown",
        "mac": "Unknown",
        "os_version": "Unknown",
        "ip_address": "10.254.0.93",
        "reachable": False,
    }]

    production_raw_response = {
        "device_detail": {
            "overallHealth": -2,
            "managementIpAddr": "10.254.0.93",
            "communicationState": "UNREACHABLE",
            "nwDeviceRole": "BORDER ROUTER",
            "nwDeviceType": "Cisco 4331 Integrated Services Router",
            "platformId": "ISR4331/K9",
            "serialNumber": "FDO2517M1EG",
            "macAddress": "6C:13:D5:BE:91:F0",
            "softwareVersion": "17.12.8",
            "nwDeviceName": "tr-ist-rtr01",
            "location": "Global/EMEA/TR Istanbul/Umut Street",
        },
        "network_device": {
            "family": "Routers",
            "softwareVersion": "17.12.8",
            "macAddress": "6c:13:d5:be:91:f0",
            "serialNumber": "FDO2517M1EG",
            "managementIpAddress": "10.254.0.93",
            "platformId": "ISR4331/K9",
            "type": "Cisco 4331 Integrated Services Router",
            "hostname": "tr-ist-rtr01",
            "reachabilityStatus": "Unreachable",
            "reachabilityFailureReason": "SNMP Connectivity Failed",
            "errorCode": "DEV-UNREACHED",
            "uptimeSeconds": 692019,
        }
    }

    mock_health = {
        "cpu": None,
        "memory": None,
        "packet_drop": None,
        "health_score": -2,
        "uptime_seconds": 692019,
        "reachable": False,
        "raw_response": production_raw_response,
    }
    mock_dnac.get_device_health.return_value = mock_health

    mock_mongo = MagicMock()
    mock_coll = MagicMock()
    mock_coll.find_one.return_value = None
    mock_mongo.get_collection.return_value = mock_coll

    with patch("dashboard.api.get_dnac_client", return_value=mock_dnac), \
         patch("dashboard.api.mongo", mock_mongo):
        res = client.get("/api/devices/10.254.0.93/telemetry")

    assert res.status_code == 200
    data = res.json()
    info = data["device_info"]

    # Site and location mapping (DNAC-05)
    assert info["site_name"] == "Istanbul"
    assert info["location_path"] == "Global/EMEA/TR Istanbul/Umut Street"
    assert info["hostname"] == "tr-ist-rtr01"

    # Deep management plane diagnostics (DNAC-04)
    diag = info["diagnostics"]
    assert diag["reachability_failure_reason"] == "SNMP Connectivity Failed"
    assert diag["error_code"] in ("NCIM12013", "DEV-UNREACHED")
    assert "SNMP request timeout" in diag["diagnostic_message"]
    assert diag["uptime_seconds"] == 692019
    # Device is alive (uptime > 7 days) but management plane SNMP is unreachable
    assert diag["is_management_plane_isolated"] is True


