# Phase 13: DNAC Client Assurance & Device Extensions — Plan

**Phase:** 13
**Status:** Planned
**Milestone:** v1.6 Live DNAC Assurance Telemetry & Asset Integration
**Requirements:** DNAC-01, DNAC-02
**Context:** `.planning/phases/13-dnac-client-assurance-device-extensions/13-CONTEXT.md`

---

## Overview

This plan extends `app/dnac_client.py` with two new DNAC query methods (`get_device_by_name_or_ip` and `get_device_health`), adds a shared `app/exceptions.py` module containing `DNACError`, `DeviceNotFoundError`, and `DNACConnectionError`, retrofits a private `_request_with_retry` 401-recovery helper into all existing client methods, and writes a suite of `@pytest.mark.integration` tests against the live DNAC appliance at `https://10.48.200.53`. No frontend or FastAPI changes occur in this phase.

---

## Files Changed

| Action | File |
|--------|------|
| CREATE | `app/exceptions.py` |
| MODIFY | `app/dnac_client.py` |
| CREATE | `tests/test_dnac_client_integration.py` |

---

## Tasks

### Task 1 — Create `app/exceptions.py`

**File:** `app/exceptions.py`
**Type:** create

#### Steps

Create `app/exceptions.py` with the following content exactly:

```python
"""
Custom exceptions for the DNAC client.

Hierarchy:
    DNACError
    ├── DeviceNotFoundError   — no device matched the supplied identifier
    └── DNACConnectionError   — DNAC unreachable, HTTP error, or auth failure
"""


class DNACError(Exception):
    """Base exception for all DNAC client errors."""


class DeviceNotFoundError(DNACError):
    """
    Raised when a DNAC query returns zero matching devices.

    Attributes:
        identifier: The hostname or IP that was searched for.
    """

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"No device found in DNAC matching: {identifier}")


class DNACConnectionError(DNACError):
    """
    Raised when the DNAC API is unreachable, returns an unexpected HTTP
    error (non-401 after retry, 404 on health lookup, 5xx, etc.), or when
    a network-level exception occurs.
    """
```

#### Verification
- `python -c "from app.exceptions import DNACError, DeviceNotFoundError, DNACConnectionError; print('OK')"` prints `OK` without errors.
- `DeviceNotFoundError("switch-1").identifier == "switch-1"` is `True`.
- `str(DeviceNotFoundError("switch-1")) == "No device found in DNAC matching: switch-1"` is `True`.

---

### Task 2 — Add `_request_with_retry` Helper + Import exceptions

**File:** `app/dnac_client.py`
**Type:** modify

#### Steps

**2a.** Add `import re` to the top-level imports block (after `import os`):

```python
import re
```

**2b.** Add `from app.exceptions import DeviceNotFoundError, DNACConnectionError` to the imports:

```python
from app.exceptions import DeviceNotFoundError, DNACConnectionError
```

**2c.** Add the `_request_with_retry` private method to the `DNACClient` class, immediately after `_get_headers` (around line 63):

```python
    def _request_with_retry(self, method: str, url: str, **kwargs) -> "requests.Response":
        """
        Make an HTTP request with automatic one-shot 401 token retry.

        On the first 401 response the cached token is cleared, a fresh token
        is fetched via ``authenticate()``, and the request is retried once.
        If the retry also returns 401 the response is returned as-is for the
        caller to handle (raise_for_status or explicit check).

        All requests are made with ``verify=self.verify_ssl`` and the
        ``X-Auth-Token`` header provided by ``_get_headers()``.
        """
        kwargs.setdefault("verify", self.verify_ssl)
        response = requests.request(method, url, headers=self._get_headers(), **kwargs)
        if response.status_code == 401:
            logger.warning(
                f"DNAC returned 401 for {method} {url} — clearing token and re-authenticating."
            )
            self.token = None
            response = requests.request(method, url, headers=self._get_headers(), **kwargs)
        return response
```

#### Verification
- `DNACClient._request_with_retry` is accessible on the class.
- When mocked to return 401 on first call and 200 on second, `authenticate()` is called exactly once.

---

### Task 3 — Retrofit Existing Methods to Use `_request_with_retry`

**File:** `app/dnac_client.py`
**Type:** modify

#### Steps

**3a. Retrofit `get_issue_status`** (around line 223):

Replace:
```python
        response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
```
With:
```python
        response = self._request_with_retry("GET", url)
```

**3b. Retrofit `get_device_issues`** (around line 286):

Replace:
```python
            response = requests.get(url, headers=self._get_headers(), params=params, verify=self.verify_ssl)
```
With:
```python
            response = self._request_with_retry("GET", url, params=params)
```

#### Verification
- `get_issue_status` and `get_device_issues` no longer call `requests.get` directly — they go through `_request_with_retry`.
- Existing behaviour is preserved (404 returns `"NOT_FOUND"` / `[]` respectively; logging unchanged).

---

### Task 4 — Implement `get_device_by_name_or_ip`

**File:** `app/dnac_client.py`
**Type:** modify

#### Steps

Add the following method to `DNACClient`, in the **Device / Network Inventory** section (after the existing issue methods, before any EOF):

```python
    # -------------------------------------------------------------------------
    # Device / Network Inventory
    # -------------------------------------------------------------------------
    def get_device_by_name_or_ip(self, device_name_or_ip: str) -> list:
        """
        Query DNAC for one or more network devices matching a hostname or
        management IP address.

        Parameters
        ----------
        device_name_or_ip : str
            Either a plain hostname (e.g. ``"switch-core-01"``) or an IPv4
            address (e.g. ``"10.48.200.100"``).  The method auto-detects
            which DNAC query parameter to use.

        Returns
        -------
        list[dict]
            A list of device dicts.  Each dict contains curated snake_case
            keys **and** a ``raw_response`` key holding the full DNAC object:

            - ``device_id``     – DNAC UUID (str)
            - ``device_name``   – hostname (str)
            - ``ip_address``    – management IP (str)
            - ``model``         – hardware model / platform ID (str)
            - ``os_version``    – IOS / NX-OS / AireOS software version (str)
            - ``serial``        – serial number (str)
            - ``mac``           – MAC address (str)
            - ``reachable``     – ``True`` if reachabilityStatus == "Reachable" (bool)
            - ``raw_response``  – original DNAC device object (dict)

        Raises
        ------
        DeviceNotFoundError
            When DNAC returns zero matching devices.
        DNACConnectionError
            When the HTTP call fails (network error, non-2xx after retry,
            except 401 which is auto-retried once).
        """
        url = f"{self.base_url}/dna/intent/api/v1/network-device"

        # Smart IPv4 vs hostname routing (D-04)
        _IPV4_RE = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        if re.fullmatch(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", device_name_or_ip):
            params = {"managementIpAddress": device_name_or_ip}
            logger.info(f"Detected IPv4 input — using managementIpAddress param.")
        else:
            params = {"hostname": device_name_or_ip}
            logger.info(f"Detected hostname input — using hostname param.")

        logger.info(
            f"DNAC Request:\n"
            f"  Method: GET\n"
            f"  URL: {url}\n"
            f"  Params: {json.dumps(params)}"
        )

        try:
            response = self._request_with_retry("GET", url, params=params)
        except Exception as exc:
            raise DNACConnectionError(
                f"Network error querying DNAC /network-device for '{device_name_or_ip}': {exc}"
            ) from exc

        logger.info(
            f"DNAC Response:\n"
            f"  Status Code: {response.status_code}\n"
            f"  Body: {response.text[:500]}"
        )

        if not response.ok:
            raise DNACConnectionError(
                f"DNAC returned HTTP {response.status_code} for device lookup "
                f"'{device_name_or_ip}': {response.text[:200]}"
            )

        data = response.json()
        raw_list = data.get("response", data)

        if isinstance(raw_list, dict):
            raw_list = [raw_list]
        if not isinstance(raw_list, list):
            raw_list = []

        # D-02: zero matches → raise
        if not raw_list:
            logger.info(f"DNAC returned zero devices for '{device_name_or_ip}'.")
            raise DeviceNotFoundError(device_name_or_ip)

        # D-05: curate + preserve raw
        devices = []
        for raw in raw_list:
            reachability = str(raw.get("reachabilityStatus", "")).lower()
            devices.append({
                "device_id":   raw.get("id", ""),
                "device_name": raw.get("hostname", raw.get("hostname", "")),
                "ip_address":  raw.get("managementIpAddress", ""),
                "model":       raw.get("platformId", raw.get("type", "")),
                "os_version":  raw.get("softwareVersion", ""),
                "serial":      raw.get("serialNumber", ""),
                "mac":         raw.get("macAddress", ""),
                "reachable":   reachability == "reachable",
                "raw_response": raw,
            })

        logger.info(
            f"get_device_by_name_or_ip: found {len(devices)} device(s) "
            f"for '{device_name_or_ip}'."
        )
        return devices
```

#### Verification
- Calling the method with a valid hostname returns a `list` with at least one dict.
- Each dict contains all 9 keys (`device_id`, `device_name`, `ip_address`, `model`, `os_version`, `serial`, `mac`, `reachable`, `raw_response`).
- An unknown hostname raises `DeviceNotFoundError`.
- A network error raises `DNACConnectionError`.

---

### Task 5 — Implement `get_device_health`

**File:** `app/dnac_client.py`
**Type:** modify

#### Steps

Add the following method to `DNACClient`, immediately after `get_device_by_name_or_ip`:

```python
    def get_device_health(self, device_id: str) -> dict:
        """
        Retrieve live assurance telemetry health metrics for a device UUID.

        Parameters
        ----------
        device_id : str
            The DNAC UUID of the device (``id`` field from the
            ``/network-device`` response).  Use
            ``get_device_by_name_or_ip()`` to resolve hostname → UUID first.

        Returns
        -------
        dict
            A normalized telemetry dict containing:

            - ``cpu_utilization``      – CPU usage % (float | None)
            - ``memory_utilization``   – Memory usage % (float | None)
            - ``packet_drop``          – Interface packet drop % (float | None)
            - ``health_score``         – DNAC 0-10 health score (int | None)
            - ``interface_error_count``– Count of errored interfaces (int | None)
            - ``poe_status``           – PoE status string (str | None)
            - ``uptime_seconds``       – Device uptime in seconds (int | None)
            - ``reachable``            – Reachability boolean (bool)
            - ``raw_response``         – Full DNAC device-health object (dict)

        Raises
        ------
        DNACConnectionError
            When DNAC returns HTTP 404 (unknown UUID), 5xx, network error,
            or any non-2xx response after the 401 retry.
        """
        url = f"{self.base_url}/dna/intent/api/v1/device-health"
        params = {"deviceRole": "ALL"}  # DNAC /device-health uses deviceRole + deviceId filter

        # DNAC device-health endpoint: filtered by querying and matching device id
        # We use the /device-health endpoint and filter by deviceId in the response
        # The endpoint accepts ?deviceRole=ALL and returns all devices; we filter by id.
        # For targeted lookup by UUID, use: GET /dna/intent/api/v1/device-health?deviceRole=ALL
        # and filter from the response, OR use the single-device endpoint if available.
        # Using the direct per-device endpoint: /dna/intent/api/v1/device-health (with deviceId query)
        params = {"deviceId": device_id}

        logger.info(
            f"DNAC Request:\n"
            f"  Method: GET\n"
            f"  URL: {url}\n"
            f"  Params: {json.dumps(params)}"
        )

        try:
            response = self._request_with_retry("GET", url, params=params)
        except Exception as exc:
            raise DNACConnectionError(
                f"Network error querying DNAC /device-health for UUID '{device_id}': {exc}"
            ) from exc

        logger.info(
            f"DNAC Response:\n"
            f"  Status Code: {response.status_code}\n"
            f"  Body: {response.text[:500]}"
        )

        if response.status_code == 404:
            raise DNACConnectionError(
                f"DNAC returned 404 — device UUID '{device_id}' not found in /device-health."
            )

        if not response.ok:
            raise DNACConnectionError(
                f"DNAC returned HTTP {response.status_code} for /device-health "
                f"UUID '{device_id}': {response.text[:200]}"
            )

        data = response.json()
        raw_obj = data.get("response", data)

        # /device-health may return a list or a dict depending on DNAC version
        if isinstance(raw_obj, list):
            if not raw_obj:
                raise DNACConnectionError(
                    f"DNAC /device-health returned empty list for UUID '{device_id}'."
                )
            raw_obj = raw_obj[0]

        # Field extraction (D-10) — key names vary by DNAC version; use .get with fallbacks
        def _float(val):
            try:
                return float(val) if val is not None else None
            except (TypeError, ValueError):
                return None

        def _int(val):
            try:
                return int(val) if val is not None else None
            except (TypeError, ValueError):
                return None

        reachability = str(raw_obj.get("reachabilityStatus", raw_obj.get("reachability", ""))).lower()

        health = {
            "cpu_utilization":       _float(raw_obj.get("cpuUtilization") or raw_obj.get("cpu")),
            "memory_utilization":    _float(raw_obj.get("memoryUtilization") or raw_obj.get("memory")),
            "packet_drop":           _float(raw_obj.get("packetLossPercent") or raw_obj.get("packetDropPercent")),
            "health_score":          _int(
                                         (raw_obj.get("overallHealth") or {}).get("score")
                                         if isinstance(raw_obj.get("overallHealth"), dict)
                                         else raw_obj.get("overallHealth") or raw_obj.get("healthScore")
                                     ),
            "interface_error_count": _int(raw_obj.get("interfaceIssueCount") or raw_obj.get("errorCount")),
            "poe_status":            str(raw_obj.get("poeStatus", raw_obj.get("poePower", "UNKNOWN"))),
            "uptime_seconds":        _int(raw_obj.get("uptimeSeconds") or raw_obj.get("upTime")),
            "reachable":             reachability in ("reachable", "true", "yes"),
            "raw_response":          raw_obj,
        }

        logger.info(
            f"get_device_health: UUID={device_id} "
            f"health_score={health['health_score']} "
            f"cpu={health['cpu_utilization']}% "
            f"mem={health['memory_utilization']}% "
            f"reachable={health['reachable']}"
        )
        return health
```

#### Verification
- Returns a dict with all 9 keys when called with a valid UUID.
- Raises `DNACConnectionError` on 404.
- `reachable` key is a `bool`.
- All numeric fields are `float`/`int` or `None` (never raw strings).

---

### Task 6 — Write Integration Tests

**File:** `tests/test_dnac_client_integration.py`
**Type:** create

#### Steps

Create `tests/test_dnac_client_integration.py` with the following content:

```python
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
# Fixtures
# ---------------------------------------------------------------------------

def _load_client() -> DNACClient:
    """Load DNACClient from config.yaml + environment variables."""
    config_path = os.path.join(project_root, "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    dnac_cfg = config.get("dnac", {})
    # Credentials come from environment (DNAC_USERNAME / DNAC_PASSWORD)
    return DNACClient(dnac_cfg)


@pytest.fixture(scope="module")
def client():
    """Shared DNACClient instance for all tests in this module."""
    if not os.environ.get("DNAC_USERNAME"):
        pytest.skip("DNAC_USERNAME not set — skipping integration tests")
    return _load_client()


@pytest.fixture(scope="module")
def known_device(client):
    """
    Returns a real device dict from DNAC.
    Discovers a live device by querying all devices and picking the first one.
    Uses get_device_by_name_or_ip with a real hostname after discovery.
    """
    import requests, urllib3
    urllib3.disable_warnings()
    token = client.authenticate()
    url = f"{client.base_url}/dna/intent/api/v1/network-device"
    resp = requests.get(url, headers={"x-auth-token": token, "Accept": "application/json"},
                        verify=client.verify_ssl)
    resp.raise_for_status()
    devices_raw = resp.json().get("response", [])
    if not devices_raw:
        pytest.skip("No devices found in DNAC — cannot run integration tests")
    first = devices_raw[0]
    return first  # raw DNAC object


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_authenticate_returns_token(client):
    """DNACClient.authenticate() returns a non-empty token string."""
    token = client.authenticate()
    assert isinstance(token, str), "Token should be a string"
    assert len(token) > 10, "Token should be non-trivial length"
    assert client.token == token, "Token should be cached on self.token"


@pytest.mark.integration
def test_get_device_by_hostname(client, known_device):
    """get_device_by_name_or_ip returns a list with the expected device for a real hostname."""
    hostname = known_device.get("hostname")
    if not hostname:
        pytest.skip("Known device has no hostname field")

    results = client.get_device_by_name_or_ip(hostname)

    assert isinstance(results, list), "Should return a list"
    assert len(results) >= 1, "Should return at least one device"

    device = results[0]
    assert "device_id" in device
    assert "device_name" in device
    assert "ip_address" in device
    assert "model" in device
    assert "os_version" in device
    assert "serial" in device
    assert "mac" in device
    assert "reachable" in device
    assert "raw_response" in device
    assert isinstance(device["reachable"], bool)
    assert isinstance(device["raw_response"], dict)


@pytest.mark.integration
def test_get_device_by_ip(client, known_device):
    """get_device_by_name_or_ip routes correctly for an IPv4 management address."""
    ip = known_device.get("managementIpAddress")
    if not ip:
        pytest.skip("Known device has no managementIpAddress")

    results = client.get_device_by_name_or_ip(ip)
    assert isinstance(results, list)
    assert len(results) >= 1
    # The returned device IP should match
    assert any(d["ip_address"] == ip for d in results), (
        f"Expected IP {ip} in results, got: {[d['ip_address'] for d in results]}"
    )


@pytest.mark.integration
def test_get_device_by_fake_hostname_raises_device_not_found(client):
    """get_device_by_name_or_ip raises DeviceNotFoundError for a non-existent hostname."""
    fake_hostname = "FAKE-DEVICE-DOES-NOT-EXIST-99999"
    with pytest.raises(DeviceNotFoundError) as exc_info:
        client.get_device_by_name_or_ip(fake_hostname)
    assert fake_hostname in str(exc_info.value)


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
        "uptime_seconds", "reachable", "raw_response"
    ]
    for key in expected_keys:
        assert key in health, f"Missing key: {key}"

    assert isinstance(health["reachable"], bool)
    assert isinstance(health["raw_response"], dict)

    # Numeric fields should be float/int or None — never raw string
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
    Simulate 401 retry: manually expire the token and verify a subsequent
    API call succeeds (re-authenticates transparently).
    """
    # Force token expiry by corrupting it
    client.token = "EXPIRED_TOKEN_TRIGGER_401"
    try:
        # Any API call should trigger the retry mechanism
        # Use get_issue_status with a dummy ID — it may return NOT_FOUND but
        # should NOT raise due to auth failure if retry works
        result = client.get_issue_status("dummy-issue-id-for-401-test")
        # After retry the token must be valid (not the corrupted one)
        assert client.token != "EXPIRED_TOKEN_TRIGGER_401", (
            "Token should have been refreshed after 401"
        )
    except Exception as exc:
        # If DNAC rejects the dummy issue, that's fine — auth should have succeeded
        # The token should be refreshed regardless
        if "401" in str(exc) or "Unauthorized" in str(exc):
            pytest.fail(f"Token retry mechanism failed — still getting 401: {exc}")
        # Other errors (e.g. 404 for dummy issue) are acceptable
        assert client.token != "EXPIRED_TOKEN_TRIGGER_401", (
            "Token should have been refreshed even if the request failed for other reasons"
        )
```

#### Verification
- `pytest tests/test_dnac_client_integration.py -m integration -v` runs all 7 tests when `DNAC_USERNAME` and `DNAC_PASSWORD` are set.
- `pytest tests/test_dnac_client_integration.py -m integration` skips all tests in CI where `DNAC_USERNAME` is absent.
- No test imports mock or patch — all hit the real appliance.

---

## UAT Criteria

1. **`app/exceptions.py` exists** with `DNACError`, `DeviceNotFoundError`, and `DNACConnectionError`.
2. **`DeviceNotFoundError("switch-1")`** produces the message `"No device found in DNAC matching: switch-1"`.
3. **`DNACClient` imports cleanly** — `from app.dnac_client import DNACClient` raises no `ImportError`.
4. **`get_device_by_name_or_ip("10.48.200.X")`** with a real device IP returns a non-empty list with all 9 keys in each dict.
5. **`get_device_by_name_or_ip("switch-hostname")`** with a real hostname returns the correct device.
6. **`get_device_by_name_or_ip("FAKE-DEVICE-DOES-NOT-EXIST")`** raises `DeviceNotFoundError`.
7. **`get_device_health(valid_uuid)`** returns a dict with all 9 keys; `reachable` is `bool`; numeric fields are `float`/`int`/`None`.
8. **`get_device_health("00000000-...")`** raises `DNACConnectionError`.
9. **Corrupting `client.token`** and calling any method causes silent re-authentication and successful response.
10. **`pytest tests/test_dnac_client_integration.py -m integration -v`** passes all 7 tests with live DNAC credentials.

---

## Threat Model

<threat_model>

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Credentials logged in plain text | HIGH | `authenticate()` already redacts credentials in logs (confirmed in existing code). New methods never log `DNAC_USERNAME`/`DNAC_PASSWORD`. |
| Token cached in memory after process restart | LOW | Token is short-lived (Cisco DNAC tokens expire in ~60min). The retry mechanism re-fetches automatically on 401. |
| Unvalidated IPv4 input could be injection vector | LOW | Input is passed as a URL query parameter via `requests` library, which URL-encodes values. No shell or SQL involved. |
| Integration tests hitting production DNAC | MEDIUM | Tests use `@pytest.mark.integration` and are skipped when `DNAC_USERNAME` is absent. CI should never set this variable. |
| SSL verification disabled by default | MEDIUM | Controlled by `config.yaml` `dnac.verify_ssl`. Documented. Appropriate for internal lab with self-signed certs. |

</threat_model>

---

## Nyquist Validation

| Task | Edge Cases | Error States |
|------|-----------|--------------|
| T1: exceptions.py | Class hierarchy correct? Base exception reusable by future callers? | Import failure if `app/` not on `sys.path` |
| T2: _request_with_retry | What if `authenticate()` itself throws on retry? Raises from `authenticate()` propagate naturally. | Infinite loop impossible — retry happens exactly once. |
| T3: Retrofit | Existing tests (if any) still pass with retrofitted methods? | `get_device_issues` wraps in try/except — ensure retry doesn't bypass the exception handler. |
| T4: get_device_by_name_or_ip | IPv4 `re.fullmatch` avoids matching `10.48.x` inside a hostname like `host10.48.x.com`? Yes — fullmatch requires the entire string to be digits+dots. | DNAC may return `{ "response": null }` — guarded by `isinstance(raw_list, list)` check. |
| T5: get_device_health | DNAC /device-health field names vary by firmware version — `_float`/`_int` helpers + `.get` fallbacks handle gracefully. | Empty list response → raises `DNACConnectionError` with clear message. |
| T6: Integration tests | `known_device` fixture discovers live device dynamically — no hardcoded hostname. Tests skip rather than fail if DNAC has no devices. | `test_token_retry_on_401` accepts non-auth exceptions as acceptable (e.g. 404 on dummy issue ID). |

---

*Plan written: 2026-10-05*
*Phase: 13-dnac-client-assurance-device-extensions*
