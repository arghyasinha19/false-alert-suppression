"""
Integration tests for DNACClient — hit the real DNAC appliance.

Run with:
    pytest tests/test_dnac_client_integration.py -m integration -v

Requires DNAC_USERNAME and DNAC_PASSWORD in the environment (or .env file).
Tests are skipped automatically in CI (no DNAC_USERNAME set).

DNAC base URL: https://10.48.200.53
"""

import os
import sys
import pytest
import yaml

# Ensure project root is on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.dnac_client import DNACClient
from app.exceptions import DeviceNotFoundError, DNACConnectionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_client() -> DNACClient:
    """Load DNACClient from config.yaml + environment variables."""
    config_path = os.path.join(project_root, "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    dnac_cfg = config.get("dnac", {})
    # Credentials come from DNAC_USERNAME / DNAC_PASSWORD environment variables
    return DNACClient(dnac_cfg)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Shared DNACClient instance for all tests in this module."""
    if not os.environ.get("DNAC_USERNAME"):
        pytest.skip("DNAC_USERNAME not set — skipping integration tests")
    return _load_client()


@pytest.fixture(scope="module")
def known_device(client):
    """
    Returns the first raw DNAC device object from a live /network-device query.
    Discovers a live device dynamically — no hardcoded hostname.
    Skips the module if DNAC has no devices.
    """
    import requests as _requests
    import urllib3
    urllib3.disable_warnings()
    token = client.authenticate()
    url = f"{client.base_url}/dna/intent/api/v1/network-device"
    resp = _requests.get(
        url,
        headers={"x-auth-token": token, "Accept": "application/json"},
        verify=client.verify_ssl,
    )
    resp.raise_for_status()
    devices_raw = resp.json().get("response", [])
    if not devices_raw:
        pytest.skip("No devices found in DNAC — cannot run integration tests")
    return devices_raw[0]  # raw DNAC object


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_authenticate_returns_token(client):
    """DNACClient.authenticate() returns a non-empty token string and caches it."""
    token = client.authenticate()
    assert isinstance(token, str), "Token should be a string"
    assert len(token) > 10, "Token should be non-trivial length"
    assert client.token == token, "Token should be cached on self.token"


@pytest.mark.integration
def test_get_device_by_hostname(client, known_device):
    """get_device_by_name_or_ip returns list with correct device for a real hostname."""
    hostname = known_device.get("hostname")
    if not hostname:
        pytest.skip("Known device has no hostname field")

    results = client.get_device_by_name_or_ip(hostname)

    assert isinstance(results, list), "Should return a list"
    assert len(results) >= 1, "Should return at least one device"

    device = results[0]
    required_keys = [
        "device_id", "device_name", "ip_address", "model",
        "os_version", "serial", "mac", "reachable", "raw_response",
    ]
    for key in required_keys:
        assert key in device, f"Missing key in returned device dict: {key}"

    assert isinstance(device["reachable"], bool), "reachable should be bool"
    assert isinstance(device["raw_response"], dict), "raw_response should be dict"


@pytest.mark.integration
def test_get_device_by_ip(client, known_device):
    """get_device_by_name_or_ip routes correctly for an IPv4 management address."""
    ip = known_device.get("managementIpAddress")
    if not ip:
        pytest.skip("Known device has no managementIpAddress")

    results = client.get_device_by_name_or_ip(ip)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any(d["ip_address"] == ip for d in results), (
        f"Expected IP {ip} in results, got: {[d['ip_address'] for d in results]}"
    )


@pytest.mark.integration
def test_get_device_by_fake_hostname_raises_device_not_found(client):
    """get_device_by_name_or_ip raises DeviceNotFoundError for a non-existent hostname."""
    fake_hostname = "FAKE-DEVICE-DOES-NOT-EXIST-99999"
    with pytest.raises(DeviceNotFoundError) as exc_info:
        client.get_device_by_name_or_ip(fake_hostname)
    assert fake_hostname in str(exc_info.value), (
        "DeviceNotFoundError message should contain the queried identifier"
    )
    assert exc_info.value.identifier == fake_hostname


@pytest.mark.integration
def test_get_device_health_valid_uuid(client, known_device):
    """get_device_health returns a complete telemetry dict for a valid device UUID."""
    device_uuid = known_device.get("id")
    if not device_uuid:
        pytest.skip("Known device has no 'id' field")

    health = client.get_device_health(device_uuid)

    assert isinstance(health, dict)
    expected_keys = [
        "cpu_utilization", "memory_utilization", "packet_drop",
        "health_score", "interface_error_count", "poe_status",
        "uptime_seconds", "reachable", "raw_response",
    ]
    for key in expected_keys:
        assert key in health, f"Missing key in health dict: {key}"

    assert isinstance(health["reachable"], bool), "reachable should be bool"
    assert isinstance(health["raw_response"], dict), "raw_response should be dict"
    assert isinstance(health["poe_status"], str), "poe_status should be str"

    # Numeric fields must be float/int or None — never raw strings
    for field in ("cpu_utilization", "memory_utilization", "packet_drop"):
        assert health[field] is None or isinstance(health[field], float), (
            f"{field} should be float or None, got {type(health[field])}"
        )
    for field in ("health_score", "interface_error_count", "uptime_seconds"):
        assert health[field] is None or isinstance(health[field], int), (
            f"{field} should be int or None, got {type(health[field])}"
        )


@pytest.mark.integration
def test_get_device_health_invalid_uuid_raises_connection_error(client):
    """get_device_health raises DNACConnectionError for a garbage UUID."""
    garbage_uuid = "00000000-0000-0000-0000-000000000000"
    with pytest.raises(DNACConnectionError):
        client.get_device_health(garbage_uuid)


@pytest.mark.integration
def test_token_retry_on_401(client):
    """
    Simulate 401 retry: corrupt the cached token and verify the next API
    call re-authenticates transparently.
    """
    # Force token expiry by corrupting it
    client.token = "EXPIRED_TOKEN_TRIGGER_401"
    try:
        # Any API call should trigger the retry mechanism.
        # get_issue_status with a dummy ID may return NOT_FOUND but should
        # NOT raise due to auth failure if retry works.
        client.get_issue_status("dummy-issue-id-for-401-test")
        assert client.token != "EXPIRED_TOKEN_TRIGGER_401", (
            "Token should have been refreshed after 401"
        )
    except Exception as exc:
        # Non-auth exceptions (e.g. 404 for dummy issue ID) are acceptable.
        if "401" in str(exc) or "Unauthorized" in str(exc).lower():
            pytest.fail(f"Token retry mechanism failed — still getting 401: {exc}")
        # Verify token was refreshed regardless of the other error
        assert client.token != "EXPIRED_TOKEN_TRIGGER_401", (
            "Token should have been refreshed even if the request failed for other reasons"
        )
