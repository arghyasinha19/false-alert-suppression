import json
import re
import logging
import os
from typing import Optional
from urllib.parse import urlparse, parse_qs

import requests
from requests.auth import HTTPBasicAuth

from app.exceptions import DeviceNotFoundError, DNACConnectionError

logger = logging.getLogger(__name__)

# Default (connect, read) timeout for every DNAC call. Without a timeout a
# hung DNAC blocks Jenkins jobs / API workers indefinitely.
DEFAULT_TIMEOUT = (10, 30)

# Issue status values that mean "no longer needs attention".
CLOSED_ISSUE_STATUSES = {"RESOLVED", "IGNORED", "CLEARED", "DELETED", "INACTIVE"}

_ISSUE_ID_RE = re.compile(r"[?&]issueId=([^&#\s]+)", re.IGNORECASE)


def extract_issue_id(event: dict) -> Optional[str]:
    """
    Pull the Assurance issueId out of a DNAC webhook event.

    The webhook ``instanceId`` identifies the *notification instance*, not the
    Assurance issue. The issue ID is carried in ``ciscoDnaEventLink``
    (``.../dna/assurance/issueDetails?issueId=<id>``) and, on some releases,
    directly in the payload / details block.
    """
    if not isinstance(event, dict):
        return None

    for key in ("issueId", "issue_id"):
        if event.get(key):
            return str(event[key])

    details = event.get("details") or {}
    if isinstance(details, dict):
        for key in ("Assurance Issue ID", "Assurance Issue Id", "issueId", "Issue ID"):
            if details.get(key):
                return str(details[key])

    link = event.get("ciscoDnaEventLink") or event.get("cisco_dna_event_link") or ""
    if isinstance(link, str) and link:
        # issueId may be in the query string or in a hash-route query string
        m = _ISSUE_ID_RE.search(link)
        if m:
            return m.group(1)
        try:
            qs = parse_qs(urlparse(link).query)
            if qs.get("issueId"):
                return qs["issueId"][0]
        except Exception:
            pass
    return None


class DNACClient:
    def __init__(self, config: dict):
        self.base_url = config['base_url'].rstrip('/')
        # Read credentials from env vars first, fall back to config dict
        self.username = os.environ.get('DNAC_USERNAME') or config.get('username')
        self.password = os.environ.get('DNAC_PASSWORD') or config.get('password')

        # TLS: verify_ssl may be true/false or a path to a CA bundle.
        # DNAC_CA_BUNDLE env var overrides config so prod can supply the corporate CA.
        ca_bundle = os.environ.get('DNAC_CA_BUNDLE')
        self.verify_ssl = ca_bundle if ca_bundle else config.get('verify_ssl', True)
        if self.verify_ssl is False:
            logger.warning(
                "DNAC TLS certificate verification is DISABLED. "
                "Set dnac.verify_ssl / DNAC_CA_BUNDLE for production."
            )

        timeout_cfg = config.get('timeout_seconds')
        if isinstance(timeout_cfg, (list, tuple)) and len(timeout_cfg) == 2:
            self.timeout = tuple(timeout_cfg)
        elif isinstance(timeout_cfg, (int, float)):
            self.timeout = (min(10, timeout_cfg), timeout_cfg)
        else:
            self.timeout = DEFAULT_TIMEOUT

        self.webhook_config = config.get('webhook_registration', {})
        self.token = None
        self.subscription_id = None

        if not self.username or not self.password:
            raise ValueError(
                "DNAC credentials missing. Set DNAC_USERNAME and DNAC_PASSWORD in your .env file."
            )

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------
    def authenticate(self) -> str:
        """Fetch and cache a DNAC auth token."""
        url = f"{self.base_url}/dna/system/api/v1/auth/token"
        logger.info(f"Authenticating with DNAC: POST {url}")
        response = requests.post(
            url,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify_ssl,
            timeout=self.timeout,
        )
        logger.info(f"DNAC auth response: {response.status_code}")
        response.raise_for_status()
        self.token = response.json()['Token']
        logger.info("DNAC authentication successful.")
        return self.token

    def _get_headers(self) -> dict:
        if not self.token:
            self.authenticate()
        return {
            "x-auth-token": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with automatic one-shot 401 token retry.

        Every request gets ``verify`` and ``timeout`` defaults. On the first 401
        the cached token is cleared, a fresh token is fetched and the request is
        retried once.
        """
        kwargs.setdefault("verify", self.verify_ssl)
        kwargs.setdefault("timeout", self.timeout)
        extra_headers = kwargs.pop("headers", None) or {}
        headers = {**self._get_headers(), **extra_headers}
        response = requests.request(method, url, headers=headers, **kwargs)
        if response.status_code == 401:
            logger.warning(
                f"DNAC returned 401 for {method} {url} — clearing token and re-authenticating."
            )
            self.token = None
            headers = {**self._get_headers(), **extra_headers}
            response = requests.request(method, url, headers=headers, **kwargs)
        return response

    @staticmethod
    def _safe_json(response: requests.Response):
        try:
            return response.json()
        except ValueError:
            return None

    # -------------------------------------------------------------------------
    # Webhook Subscription Management
    # -------------------------------------------------------------------------
    def list_event_subscriptions(self) -> list:
        """
        List all current webhook subscriptions registered in DNAC.
        Returns an empty list if DNAC responds with 204 No Content.
        """
        url = f"{self.base_url}/dna/intent/api/v1/event/subscription"
        logger.info(f"DNAC Request: GET {url}")
        response = self._request_with_retry("GET", url)

        if response.status_code == 204:
            logger.info("DNAC Response: 204 (no webhook subscriptions registered yet)")
            return []

        if not response.ok:
            logger.error(f"DNAC list subscriptions failed: {response.status_code} {response.text[:500]}")
            response.raise_for_status()

        data = self._safe_json(response)
        if isinstance(data, dict):
            data = data.get("response", [])
        data = data or []
        logger.info(f"DNAC Response: {response.status_code}, {len(data)} subscription(s)")
        return data

    def register_webhook(self) -> dict:
        """
        Register this service as a REST/Webhook subscriber in DNAC.
        DNAC will push event payloads to our FastAPI receiver_url.
        This is always a manual, on-demand operation - never auto-called on startup.
        """
        receiver_url = self.webhook_config['receiver_url']
        name = self.webhook_config.get('name', 'FalseAlertDetection')
        description = self.webhook_config.get('description', '')
        event_categories = self.webhook_config.get('event_categories', [])

        if receiver_url.lower().startswith("http://"):
            logger.warning(
                "Webhook receiver_url uses plain HTTP. Use HTTPS in production so the "
                "shared-secret header and alert payloads are not sent in clear text."
            )

        subscription_filter = {}
        if event_categories:
            subscription_filter["categories"] = event_categories

        headers = [{"string": "Content-Type: application/json"}]
        # Shared secret DNAC sends with every event; validated by app/main.py.
        webhook_token = os.environ.get("WEBHOOK_AUTH_TOKEN")
        token_header = self.webhook_config.get("auth_header_name", "X-Webhook-Token")
        if webhook_token:
            headers.append({"string": f"{token_header}: {webhook_token}"})
        else:
            logger.warning("WEBHOOK_AUTH_TOKEN not set - subscription will be registered without an auth header.")

        payload = [
            {
                "name": name,
                "description": description,
                "filter": subscription_filter,
                "subscriptionDetails": {
                    "connectorType": "REST",
                    "method": "POST",
                    "url": receiver_url,
                    "headers": headers,
                }
            }
        ]

        register_url = f"{self.base_url}/dna/intent/api/v1/event/subscription/rest"
        logger.info(f"Registering webhook with DNAC. Receiver URL: {receiver_url}")

        existing = self.list_event_subscriptions()
        for sub in existing:
            if sub.get('name') == name:
                self.subscription_id = sub.get('subscriptionId')
                logger.info(f"Webhook '{name}' already registered (ID: {self.subscription_id}). Skipping.")
                return sub

        logger.info(f"DNAC Request: POST {register_url} (subscription '{name}')")
        response = self._request_with_retry("POST", register_url, json=payload)
        logger.info(f"DNAC Response: {response.status_code} {response.text[:500]}")

        if not response.ok:
            logger.error(f"DNAC rejected registration: {response.status_code} - {response.text[:1000]}")
        response.raise_for_status()

        result = self._safe_json(response) or {}
        if isinstance(result, list) and result:
            self.subscription_id = result[0].get('subscriptionId')
        elif isinstance(result, dict):
            self.subscription_id = result.get('subscriptionId')
        logger.info(f"Webhook registered successfully. Subscription ID: {self.subscription_id}")
        return result

    def deregister_webhook(self) -> None:
        """Remove the webhook subscription from DNAC."""
        if not self.subscription_id:
            return

        url = f"{self.base_url}/dna/intent/api/v1/event/subscription"
        params = {"subscriptionIds": self.subscription_id}
        logger.info(f"De-registering webhook (ID: {self.subscription_id}): DELETE {url}")
        response = self._request_with_retry("DELETE", url, params=params)
        logger.info(f"DNAC Response: {response.status_code} {response.text[:500]}")
        if response.ok:
            logger.info("Webhook de-registered successfully.")
        else:
            logger.warning(f"Failed to de-register webhook: {response.status_code} {response.text[:500]}")

    # -------------------------------------------------------------------------
    # Issue / Event Status Checks
    # -------------------------------------------------------------------------
    def get_issue_status(self, issue_id: str) -> str:
        """
        Fetch the current status of an Assurance issue by its **issueId**
        (NOT the webhook instanceId - see ``extract_issue_id``).

        Uses ``GET /dna/data/api/v1/assuranceIssues/{id}`` (Catalyst Center
        2.3.7.x+). Returns:
          - the upper-cased status (ACTIVE / RESOLVED / IGNORED)
          - ``"NOT_FOUND"`` when DNAC says the issue does not exist
          - ``"UNSUPPORTED"`` when this DNAC release does not expose the
            endpoint (caller should fall back to ``get_device_issues``)
        Raises DNACConnectionError on other errors.
        """
        if not issue_id:
            logger.warning("No issue_id provided. Cannot check DNAC status.")
            return "UNKNOWN"

        url = f"{self.base_url}/dna/data/api/v1/assuranceIssues/{issue_id}"
        logger.info(f"DNAC Request: GET {url}")
        try:
            response = self._request_with_retry("GET", url)
        except requests.RequestException as exc:
            raise DNACConnectionError(f"Network error querying DNAC issue {issue_id}: {exc}") from exc

        logger.info(f"DNAC Response: {response.status_code} {response.text[:500]}")

        if response.status_code == 404:
            # A JSON 404 body means "issue not found"; a non-JSON 404 means the
            # API path does not exist on this release.
            return "NOT_FOUND" if isinstance(self._safe_json(response), dict) else "UNSUPPORTED"
        if response.status_code in (400, 405, 501):
            return "UNSUPPORTED"
        if not response.ok:
            raise DNACConnectionError(
                f"DNAC returned HTTP {response.status_code} for issue {issue_id}: {response.text[:200]}"
            )

        data = self._safe_json(response) or {}
        resp_obj = data.get("response", data) if isinstance(data, dict) else {}
        if isinstance(resp_obj, list):
            resp_obj = resp_obj[0] if resp_obj else {}
        if not resp_obj:
            return "NOT_FOUND"
        status = str(resp_obj.get("status") or resp_obj.get("issueStatus") or "UNKNOWN").upper()
        logger.info(f"DNAC issue {issue_id} status is: {status}")
        return status

    def get_device_issues(
        self,
        device_id: str = None,
        device_name: str = None,
        issue_status: str = None,
        start_time_ms: int = None,
        end_time_ms: int = None,
    ) -> list:
        """
        Query ``GET /dna/intent/api/v1/issues`` for ONE device.

        The API filters by ``deviceId`` (Assurance device UUID) and has no
        hostname filter. Unknown parameters are silently ignored by DNAC, which
        previously caused a network-wide query. Without a device_id we refuse to
        query and return [].

        Raises DNACConnectionError on transport/HTTP errors so callers can
        distinguish "no issues" from "could not check".
        """
        if not device_id:
            logger.warning(
                f"get_device_issues called without device_id (device_name={device_name}); "
                f"refusing to run an unfiltered network-wide query."
            )
            return []

        url = f"{self.base_url}/dna/intent/api/v1/issues"
        params = {"deviceId": device_id}
        if issue_status:
            params["issueStatus"] = issue_status.upper()
        if start_time_ms:
            params["startTime"] = int(start_time_ms)
        if end_time_ms:
            params["endTime"] = int(end_time_ms)

        logger.info(f"DNAC Request: GET {url} params={json.dumps(params)}")
        try:
            response = self._request_with_retry("GET", url, params=params)
        except requests.RequestException as exc:
            raise DNACConnectionError(f"Network error querying DNAC issues for {device_id}: {exc}") from exc

        if response.status_code in (404, 204):
            logger.info(f"DNAC Response: {response.status_code} (no issues found for device)")
            return []
        if not response.ok:
            raise DNACConnectionError(
                f"DNAC returned HTTP {response.status_code} for issues of device {device_id}: "
                f"{response.text[:200]}"
            )

        data = self._safe_json(response) or {}
        resp_obj = data.get("response", data) if isinstance(data, dict) else data
        if isinstance(resp_obj, list):
            issues = resp_obj
        elif isinstance(resp_obj, dict):
            issues = [resp_obj]
        else:
            issues = []
        # Defensive: keep only issues for this device in case the filter is ignored.
        issues = [i for i in issues if isinstance(i, dict) and (not i.get("deviceId") or i.get("deviceId") == device_id)]
        logger.info(f"DNAC Response: {response.status_code}, {len(issues)} issue(s) for device {device_id}")
        return issues

    # -------------------------------------------------------------------------
    # Device / Network Inventory
    # -------------------------------------------------------------------------
    def get_device_by_name_or_ip(self, device_name_or_ip: str) -> list:
        """
        Query DNAC for one or more network devices matching a hostname or
        management IP address.

        Returns a list of device dicts with curated snake_case keys
        (device_id, device_name, ip_address, model, os_version, serial, mac,
        reachable) plus ``raw_response``.

        Raises DeviceNotFoundError when zero devices match, DNACConnectionError
        on transport / HTTP errors.
        """
        url = f"{self.base_url}/dna/intent/api/v1/network-device"

        if re.fullmatch(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", device_name_or_ip):
            params = {"managementIpAddress": device_name_or_ip}
        else:
            params = {"hostname": device_name_or_ip}

        logger.info(f"DNAC Request: GET {url} params={json.dumps(params)}")

        try:
            response = self._request_with_retry("GET", url, params=params)
        except Exception as exc:
            raise DNACConnectionError(
                f"Network error querying DNAC /network-device for '{device_name_or_ip}': {exc}"
            ) from exc

        logger.info(f"DNAC Response: {response.status_code} {response.text[:500]}")

        if not response.ok:
            raise DNACConnectionError(
                f"DNAC returned HTTP {response.status_code} for device lookup "
                f"'{device_name_or_ip}': {response.text[:200]}"
            )

        data = self._safe_json(response) or {}
        raw_list = data.get("response", data) if isinstance(data, dict) else data

        if isinstance(raw_list, dict):
            raw_list = [raw_list]
        if not isinstance(raw_list, list):
            raw_list = []

        if not raw_list:
            logger.info(f"DNAC returned zero devices for '{device_name_or_ip}'.")
            raise DeviceNotFoundError(device_name_or_ip)

        devices = []
        for raw in raw_list:
            reachability = str(raw.get("reachabilityStatus", "")).lower()
            devices.append({
                "device_id":    raw.get("id", ""),
                "device_name":  raw.get("hostname", ""),
                "ip_address":   raw.get("managementIpAddress", ""),
                "model":        raw.get("platformId", raw.get("type", "")),
                "os_version":   raw.get("softwareVersion", ""),
                "serial":       raw.get("serialNumber", ""),
                "mac":          raw.get("macAddress", ""),
                "reachable":    reachability == "reachable",
                "raw_response": raw,
            })

        logger.info(f"get_device_by_name_or_ip: found {len(devices)} device(s) for '{device_name_or_ip}'.")
        return devices

    def get_device_health(self, device_id: str) -> dict:
        """
        Retrieve assurance health metrics for ONE device UUID.

        ``/dna/intent/api/v1/device-health`` cannot filter by device (it only
        accepts deviceRole/siteId/health/time/paging), so the previous
        implementation returned whichever device DNAC listed first. We now use
        ``GET /dna/intent/api/v1/device-detail?identifier=uuid&searchBy=<uuid>``
        which is device-specific, and enrich with ``/network-device/{id}`` for
        reachability and uptime.

        Returned keys: cpu_utilization, memory_utilization, cpu, memory (aliases
        used by dashboard/device_service.py), packet_drop, health_score,
        interface_error_count, poe_status, uptime_seconds, reachable,
        raw_response. Metrics DNAC does not report are None.

        Raises DNACConnectionError on 404 (unknown UUID), 5xx, network error.
        """
        def _float(val):
            try:
                return float(val) if val not in (None, "") else None
            except (TypeError, ValueError):
                return None

        def _int(val):
            try:
                return int(float(val)) if val not in (None, "") else None
            except (TypeError, ValueError):
                return None

        def _first(d: dict, *keys):
            for k in keys:
                if d.get(k) not in (None, ""):
                    return d.get(k)
            return None

        # 1. Device detail (assurance) - device-specific
        url = f"{self.base_url}/dna/intent/api/v1/device-detail"
        params = {"identifier": "uuid", "searchBy": device_id}
        logger.info(f"DNAC Request: GET {url} params={json.dumps(params)}")
        try:
            response = self._request_with_retry("GET", url, params=params)
        except Exception as exc:
            raise DNACConnectionError(
                f"Network error querying DNAC /device-detail for UUID '{device_id}': {exc}"
            ) from exc

        logger.info(f"DNAC Response: {response.status_code} {response.text[:500]}")
        if response.status_code == 404:
            raise DNACConnectionError(f"DNAC returned 404 — device UUID '{device_id}' not found.")
        if not response.ok:
            raise DNACConnectionError(
                f"DNAC returned HTTP {response.status_code} for /device-detail "
                f"UUID '{device_id}': {response.text[:200]}"
            )
        data = self._safe_json(response) or {}
        detail = data.get("response", data) if isinstance(data, dict) else {}
        if isinstance(detail, list):
            detail = detail[0] if detail else {}
        if not detail:
            raise DNACConnectionError(f"DNAC /device-detail returned no data for UUID '{device_id}'.")

        # 2. Inventory record (reachability / uptime) - best effort
        inventory = {}
        try:
            inv_resp = self._request_with_retry(
                "GET", f"{self.base_url}/dna/intent/api/v1/network-device/{device_id}"
            )
            if inv_resp.ok:
                inv_data = self._safe_json(inv_resp) or {}
                inventory = inv_data.get("response", {}) if isinstance(inv_data, dict) else {}
        except Exception as exc:
            logger.warning(f"Inventory lookup for {device_id} failed: {exc}")

        reach_raw = str(
            _first(inventory, "reachabilityStatus")
            or _first(detail, "communicationState", "reachabilityHealth", "reachabilityStatus")
            or ""
        ).lower()
        reachable = reach_raw in ("reachable", "true", "yes", "up")

        overall = _first(detail, "overallHealth", "healthScore")
        if isinstance(overall, dict):
            overall = overall.get("score")

        cpu = _float(_first(detail, "cpu", "cpuUtilization", "cpuUlitilization"))
        mem = _float(_first(detail, "memory", "memoryUtilization"))

        health = {
            "cpu_utilization":       cpu,
            "memory_utilization":    mem,
            "cpu":                   cpu,
            "memory":                mem,
            "packet_drop":           _float(_first(detail, "packetLossPercent", "packetDropPercent")),
            "health_score":          _int(overall),
            "interface_error_count": _int(_first(detail, "interfaceIssueCount", "errorCount")),
            "poe_status":            str(_first(detail, "poeStatus", "poePower") or "UNKNOWN"),
            "uptime_seconds":        _int(_first(inventory, "uptimeSeconds")),
            "reachable":             reachable,
            "raw_response":          {"device_detail": detail, "network_device": inventory},
        }

        logger.info(
            f"get_device_health: UUID={device_id} health_score={health['health_score']} "
            f"cpu={health['cpu_utilization']} mem={health['memory_utilization']} reachable={health['reachable']}"
        )
        return health
