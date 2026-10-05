import json
import re
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import logging
import os

from app.exceptions import DeviceNotFoundError, DNACConnectionError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

class DNACClient:
    def __init__(self, config: dict):
        self.base_url = config['base_url'].rstrip('/')
        # Read credentials from env vars first, fall back to config dict
        self.username = os.environ.get('DNAC_USERNAME') or config.get('username')
        self.password = os.environ.get('DNAC_PASSWORD') or config.get('password')
        self.verify_ssl = config.get('verify_ssl', False)
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
        logger.info("Authenticating with DNAC...")
        logger.info(
            f"DNAC Request:\n"
            f"  Method: POST\n"
            f"  URL: {url}\n"
            f"  Payload: (basic-auth credentials, not logged)"
        )
        response = requests.post(
            url,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify_ssl
        )
        logger.info(
            f"DNAC Response:\n"
            f"  Status Code: {response.status_code}\n"
            f"  Body: [REDACTED AUTH TOKEN]"
        )
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

    # -------------------------------------------------------------------------
    # Webhook Subscription Management
    # -------------------------------------------------------------------------
    def list_event_subscriptions(self) -> list:
        """
        List all current webhook subscriptions registered in DNAC.
        Returns an empty list if DNAC responds with 204 No Content
        (which means no subscriptions exist yet).
        """
        url = f"{self.base_url}/dna/intent/api/v1/event/subscription"
        logger.info(
            f"DNAC Request:\n"
            f"  Method: GET\n"
            f"  URL: {url}"
        )
        response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)

        # 204 No Content = no subscriptions registered yet - not an error
        if response.status_code == 204:
            logger.info(
                f"DNAC Response:\n"
                f"  Status Code: 204 (No Content)\n"
                f"  Body: (empty — no webhook subscriptions registered yet)"
            )
            return []

        logger.info(
            f"DNAC Response:\n"
            f"  Status Code: {response.status_code}\n"
            f"  Body: {json.dumps(response.json(), indent=2)}"
        )
        response.raise_for_status()
        return response.json()

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
        
        # Build filter - only include fields DNAC actually supports
        # Leave eventIds empty to match all events in the chosen categories
        subscription_filter = {}
        if event_categories:
            subscription_filter["categories"] = event_categories
            
        # The /rest endpoint expects a list of objects exactly in this schema
        payload = [
            {
                "name": name,
                "description": description,
                "filter": subscription_filter,
                "subscriptionDetails": {
                    "connectorType": "REST",
                    "method": "POST",
                    "url": receiver_url,
                    "headers": [
                        {"string": "Content-Type: application/json"}
                    ]
                }
            }
        ]
        
        # Use the REST-specific endpoint
        register_url = f"{self.base_url}/dna/intent/api/v1/event/subscription/rest"
        
        logger.info(f"Registering webhook with DNAC. Receiver URL: {receiver_url}")
        
        # Check if already registered to avoid duplicates
        existing = self.list_event_subscriptions()
        for sub in existing:
            if sub.get('name') == name:
                self.subscription_id = sub.get('subscriptionId')
                logger.info(f"Webhook '{name}' already registered (ID: {self.subscription_id}). Skipping.")
                return sub

        logger.info(
            f"DNAC Request:\n"
            f"  Method: POST\n"
            f"  URL: {register_url}\n"
            f"  Payload: {json.dumps(payload, indent=2)}"
        )
        response = requests.post(
            register_url,
            headers=self._get_headers(),
            json=payload,
            verify=self.verify_ssl
        )
        logger.info(
            f"DNAC Response:\n"
            f"  Status Code: {response.status_code}\n"
            f"  Body: {response.text}"
        )
        
        # Log full DNAC error body for easy debugging
        if not response.ok:
            logger.error(
                f"DNAC rejected registration: {response.status_code} - {response.text}"
            )
        response.raise_for_status()
        
        result = response.json()
        self.subscription_id = (
            result[0].get('subscriptionId') if isinstance(result, list) 
            else result.get('subscriptionId')
        )
        logger.info(f"Webhook registered successfully. Subscription ID: {self.subscription_id}")
        return result
        
    def deregister_webhook(self) -> None:
        """Remove the webhook subscription from DNAC on service shutdown."""
        if not self.subscription_id:
            return
            
        url = f"{self.base_url}/dna/intent/api/v1/event/subscription"
        params = {"subscriptionIds": self.subscription_id}
        logger.info(f"De-registering webhook (ID: {self.subscription_id})...")
        logger.info(
            f"DNAC Request:\n"
            f"  Method: DELETE\n"
            f"  URL: {url}\n"
            f"  Params: {json.dumps(params, indent=2)}"
        )
        response = requests.delete(url, headers=self._get_headers(), params=params, verify=self.verify_ssl)
        logger.info(
            f"DNAC Response:\n"
            f"  Status Code: {response.status_code}\n"
            f"  Body: {response.text}"
        )
        if response.ok:
            logger.info("Webhook de-registered successfully.")
        else:
            logger.warning(f"Failed to de-register webhook: {response.status_code} {response.text}")

    # -------------------------------------------------------------------------
    # Issue / Event Status Checks
    # -------------------------------------------------------------------------
    def get_issue_status(self, issue_id: str) -> str:
        """
        Fetch the current status of an issue from DNAC.
        Returns the issue status string (e.g., 'ACTIVE', 'RESOLVED').
        If the issue is not found (404), it is assumed to be resolved.
        """
        if not issue_id:
            logger.warning("No issue_id provided. Cannot check DNAC status.")
            return "UNKNOWN"
            
        url = f"{self.base_url}/dna/intent/api/v1/issues/{issue_id}"
        logger.info(
            f"DNAC Request:\n"
            f"  Method: GET\n"
            f"  URL: {url}"
        )
        
        response = self._request_with_retry("GET", url)

        # In DNAC, an issue that is no longer active may be deleted and return 404
        if response.status_code == 404:
            logger.info(
                f"DNAC Response:\n"
                f"  Status Code: 404 (Not Found)\n"
                f"  Body: {response.text}\n"
                f"  -> Issue {issue_id} not found."
            )
            return "NOT_FOUND"
            
        if not response.ok:
            logger.error(
                f"DNAC Response (Error):\n"
                f"  Status Code: {response.status_code}\n"
                f"  Body: {response.text}"
            )
            response.raise_for_status()
            
        data = response.json()
        
        logger.info(
            f"DNAC Response:\n"
            f"  Status Code: {response.status_code}\n"
            f"  Body: {json.dumps(data, indent=2)}"
        )
        
        # The structure is usually: { "response": { "issueStatus": "ACTIVE", ... } }
        # or flat { "issueStatus": "ACTIVE" }
        resp_obj = data.get("response", data)
        status = resp_obj.get("issueStatus", "UNKNOWN")
        
        logger.info(f"DNAC issue {issue_id} status is: {status}")
        return status

    def get_device_issues(
        self,
        device_id: str = None,
        device_name: str = None,
        issue_status: str = None
    ) -> list:
        """
        Query DNAC for issues associated with a device (and optionally filtered by issueStatus).
        Returns a list of issue objects (dicts).
        """
        url = f"{self.base_url}/dna/intent/api/v1/issues"
        params = {}
        if device_id:
            params["deviceUuid"] = device_id
        if device_name:
            params["deviceName"] = device_name
        if issue_status:
            params["issueStatus"] = issue_status

        logger.info(
            f"DNAC Request:\n"
            f"  Method: GET\n"
            f"  URL: {url}\n"
            f"  Params: {json.dumps(params)}"
        )

        try:
            response = self._request_with_retry("GET", url, params=params)
            if response.status_code in (404, 204):
                logger.info(f"DNAC Response: {response.status_code} (No issues found for device)")
                return []
            response.raise_for_status()
            data = response.json()
            resp_obj = data.get("response", data)
            if isinstance(resp_obj, list):
                return resp_obj
            elif isinstance(resp_obj, dict):
                return [resp_obj]
            return []
        except Exception as e:
            logger.error(f"Failed to fetch device issues from DNAC: {e}")
            return []

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

            - ``device_id``     - DNAC UUID (str)
            - ``device_name``   - hostname (str)
            - ``ip_address``    - management IP (str)
            - ``model``         - hardware model / platform ID (str)
            - ``os_version``    - IOS / NX-OS / AireOS software version (str)
            - ``serial``        - serial number (str)
            - ``mac``           - MAC address (str)
            - ``reachable``     - True if reachabilityStatus == "Reachable" (bool)
            - ``raw_response``  - original DNAC device object (dict)

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
        if re.fullmatch(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", device_name_or_ip):
            params = {"managementIpAddress": device_name_or_ip}
            logger.info("Detected IPv4 input — using managementIpAddress param.")
        else:
            params = {"hostname": device_name_or_ip}
            logger.info("Detected hostname input — using hostname param.")

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

        # D-02: zero matches -> raise
        if not raw_list:
            logger.info(f"DNAC returned zero devices for '{device_name_or_ip}'.")
            raise DeviceNotFoundError(device_name_or_ip)

        # D-05: curate + preserve raw
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

        logger.info(
            f"get_device_by_name_or_ip: found {len(devices)} device(s) "
            f"for '{device_name_or_ip}'."
        )
        return devices

    def get_device_health(self, device_id: str) -> dict:
        """
        Retrieve live assurance telemetry health metrics for a device UUID.

        Parameters
        ----------
        device_id : str
            The DNAC UUID of the device (``id`` field from the
            ``/network-device`` response).  Use
            ``get_device_by_name_or_ip()`` to resolve hostname to UUID first.

        Returns
        -------
        dict
            A normalized telemetry dict containing:

            - ``cpu_utilization``       - CPU usage % (float | None)
            - ``memory_utilization``    - Memory usage % (float | None)
            - ``packet_drop``           - Interface packet drop % (float | None)
            - ``health_score``          - DNAC 0-10 health score (int | None)
            - ``interface_error_count`` - Count of errored interfaces (int | None)
            - ``poe_status``            - PoE status string (str)
            - ``uptime_seconds``        - Device uptime in seconds (int | None)
            - ``reachable``             - Reachability boolean (bool)
            - ``raw_response``          - Full DNAC device-health object (dict)

        Raises
        ------
        DNACConnectionError
            When DNAC returns HTTP 404 (unknown UUID), 5xx, network error,
            or any non-2xx response after the 401 retry.
        """
        url = f"{self.base_url}/dna/intent/api/v1/device-health"
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

        reachability = str(
            raw_obj.get("reachabilityStatus", raw_obj.get("reachability", ""))
        ).lower()

        overall = raw_obj.get("overallHealth")
        if isinstance(overall, dict):
            health_score_raw = overall.get("score")
        else:
            health_score_raw = overall or raw_obj.get("healthScore")

        health = {
            "cpu_utilization":       _float(raw_obj.get("cpuUtilization") or raw_obj.get("cpu")),
            "memory_utilization":    _float(raw_obj.get("memoryUtilization") or raw_obj.get("memory")),
            "packet_drop":           _float(
                                         raw_obj.get("packetLossPercent")
                                         or raw_obj.get("packetDropPercent")
                                     ),
            "health_score":          _int(health_score_raw),
            "interface_error_count": _int(
                                         raw_obj.get("interfaceIssueCount")
                                         or raw_obj.get("errorCount")
                                     ),
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

