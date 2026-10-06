"""
ServiceNow Table API client for incident correlation / creation.

Design rules (production):
  * Every call either succeeds or RAISES ServiceNowError. A failed lookup must
    never be treated as "no incident exists" (that created duplicates).
  * Incidents are de-duplicated by ``correlation_id`` (one DNAC notification ->
    at most one action), so RabbitMQ/Jenkins redelivery is idempotent.
  * Device matching is exact on the device token in short_description
    ("sw1" no longer matches "sw10").
  * State handling follows out-of-the-box incident states (configurable):
      open      = active and not Resolved/Closed/Canceled  -> append comment
      Resolved  = within reopen window                      -> reopen
      Closed / Canceled                                     -> new incident
"""
import os
import logging
from typing import Optional, List, Dict, Any

import requests

logger = logging.getLogger(__name__)

SHORT_DESC_PREFIX = "Monitoring Alert: "


class ServiceNowError(Exception):
    """Raised when ServiceNow cannot be queried or updated."""


def _env(name: str, default: str) -> str:
    val = os.getenv(name)
    return val if val not in (None, "") else default


def _verify_setting():
    val = _env("SNOW_VERIFY_TLS", "true").strip()
    if val.lower() in ("false", "0", "no"):
        return False
    if val.lower() in ("true", "1", "yes"):
        return True
    return val  # path to CA bundle


def _q(value: str) -> str:
    """Neutralise characters that have meaning in an encoded query."""
    return str(value or "").replace("^", " ").replace("\n", " ").strip()


class ServiceNowClient:
    def __init__(self):
        self.base_url = os.getenv("SNOW_INSTANCE_URL", "").rstrip("/")
        self.username = os.getenv("SNOW_USERNAME", "")
        self.password = os.getenv("SNOW_PASSWORD", "")
        self.timeout = int(_env("SNOW_TIMEOUT_SECONDS", "20"))
        self.verify = _verify_setting()

        # Incident field values - confirm these against the PROD instance.
        self.cmdb_ci = _env("SNOW_CMDB_CI", "Network")
        self.contact_type = _env("SNOW_CONTACT_TYPE", "Monitoring")
        self.assignment_group = _env("SNOW_ASSIGNMENT_GROUP", "Global - CITO Network Services - Dyson")
        # NOTE: original value kept as default; "Inciden_" looks like a typo -
        # set SNOW_CATEGORY to the exact choice value used in prod.
        self.category = _env("SNOW_CATEGORY", "Inciden_Infrastructure & Network")
        self.subcategory = _env("SNOW_SUBCATEGORY", "IT Enabling")
        self.subcategory_2 = _env("SNOW_SUBCATEGORY_2", "Event")

        # Out-of-the-box incident state values.
        self.state_resolved = _env("SNOW_RESOLVED_STATE", "6")
        self.state_closed = _env("SNOW_CLOSED_STATE", "7")
        self.state_canceled = _env("SNOW_CANCELED_STATE", "8")
        self.state_reopen = _env("SNOW_REOPEN_STATE", "1")

        self.set_impact_urgency = _env("SNOW_SET_IMPACT_URGENCY", "false").lower() in ("1", "true", "yes")

        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.username and self.password)

    def _require_config(self):
        if not self.configured:
            raise ServiceNowError(
                "ServiceNow is not configured (SNOW_INSTANCE_URL / SNOW_USERNAME / SNOW_PASSWORD)."
            )

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        self._require_config()
        url = f"{self.base_url}{path}"
        try:
            resp = requests.request(
                method, url,
                auth=(self.username, self.password),
                headers=self.headers,
                timeout=self.timeout,
                verify=self.verify,
                **kwargs,
            )
        except requests.RequestException as e:
            raise ServiceNowError(f"ServiceNow {method} {path} failed: {e}") from e
        if not resp.ok:
            raise ServiceNowError(f"ServiceNow {method} {path} returned {resp.status_code}: {resp.text[:500]}")
        try:
            return resp.json()
        except ValueError as e:
            raise ServiceNowError(f"ServiceNow {method} {path} returned non-JSON body") from e

    def _base_query(self) -> List[str]:
        return [
            f"cmdb_ci={_q(self.cmdb_ci)}^ORcmdb_ci.name={_q(self.cmdb_ci)}",
            f"contact_type={_q(self.contact_type)}",
            f"assignment_group.name={_q(self.assignment_group)}",
            f"category={_q(self.category)}",
            f"subcategory={_q(self.subcategory)}",
            f"u_subcategory_2={_q(self.subcategory_2)}",
        ]

    def _query(self, parts: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        params = {
            "sysparm_query": "^".join(parts) + "^ORDERBYDESCsys_created_on",
            "sysparm_limit": str(limit),
            "sysparm_fields": "sys_id,number,state,active,short_description,correlation_id,resolved_at,closed_at",
            "sysparm_display_value": "false",
        }
        data = self._request("GET", "/api/now/table/incident", params=params)
        return data.get("result", []) or []

    @staticmethod
    def short_description_for(device_name: str) -> str:
        return f"{SHORT_DESC_PREFIX}{device_name}"

    @staticmethod
    def _is_same_device(incident: Dict[str, Any], device_name: str) -> bool:
        """Exact device match on short_description (prevents sw1 matching sw10)."""
        sd = str(incident.get("short_description") or "").strip()
        expected = f"{SHORT_DESC_PREFIX}{device_name}"
        return sd.lower() == expected.lower() or sd.lower().startswith(expected.lower() + " ")

    def _device_query(self, device_name: str) -> str:
        return f"short_descriptionSTARTSWITH{_q(SHORT_DESC_PREFIX + device_name)}"

    # ------------------------------------------------------------------
    # Lookups (all raise ServiceNowError on failure)
    # ------------------------------------------------------------------
    def find_by_correlation_id(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        if not correlation_id:
            return None
        rows = self._query([f"correlation_id={_q(correlation_id)}"], limit=1)
        return rows[0] if rows else None

    def find_open_incident(self, device_name: str) -> Optional[Dict[str, Any]]:
        parts = self._base_query() + [
            self._device_query(device_name),
            "active=true",
            f"stateNOT IN{self.state_resolved},{self.state_closed},{self.state_canceled}",
        ]
        for row in self._query(parts):
            if self._is_same_device(row, device_name):
                return row
        return None

    def find_recently_resolved_incident(self, device_name: str, within_days: int = 3) -> Optional[Dict[str, Any]]:
        parts = self._base_query() + [
            self._device_query(device_name),
            f"state={self.state_resolved}",
            f"resolved_at>=javascript:gs.daysAgoStart({int(within_days)})",
        ]
        for row in self._query(parts):
            if self._is_same_device(row, device_name):
                return row
        return None

    def find_recently_closed_incident(self, device_name: str, within_days: int = 3) -> Optional[Dict[str, Any]]:
        parts = self._base_query() + [
            self._device_query(device_name),
            f"state={self.state_closed}",
            f"closed_at>=javascript:gs.daysAgoStart({int(within_days)})",
        ]
        for row in self._query(parts):
            if self._is_same_device(row, device_name):
                return row
        return None

    # Backwards-compatible wrapper used elsewhere in the codebase
    def find_incident(self, device_name: str, active: bool = True, closed_within_days: int = None):
        if active:
            return self.find_open_incident(device_name)
        return self.find_recently_resolved_incident(device_name, closed_within_days or 3)

    # ------------------------------------------------------------------
    # Mutations (all raise ServiceNowError on failure)
    # ------------------------------------------------------------------
    def append_comment(self, incident_sys_id: str, comment: str, work_note: bool = False) -> Dict[str, Any]:
        field = "work_notes" if work_note else "comments"
        data = self._request("PATCH", f"/api/now/table/incident/{incident_sys_id}", json={field: comment})
        return data.get("result", {})

    def reopen_incident(self, incident_sys_id: str, comment: str) -> Dict[str, Any]:
        payload = {"state": self.state_reopen, "incident_state": self.state_reopen, "comments": comment}
        data = self._request("PATCH", f"/api/now/table/incident/{incident_sys_id}", json=payload)
        result = data.get("result", {})
        # Business rules can silently refuse a state change; verify it.
        new_state = str(result.get("state", ""))
        if new_state in (self.state_resolved, self.state_closed, self.state_canceled):
            raise ServiceNowError(
                f"Reopen of {incident_sys_id} was not applied (state still {new_state}); "
                f"check business rules / ACLs for the integration user."
            )
        return result

    def create_incident(
        self,
        device_name: str,
        issue_description: str,
        raw_alert: str,
        correlation_id: Optional[str] = None,
        severity: Optional[str] = None,
        related_incident: Optional[str] = None,
    ) -> Dict[str, Any]:
        description = f"Issue: {issue_description}\n\n"
        if related_incident:
            description += f"Related (closed) incident: {related_incident}\n\n"
        description += f"Raw Alert:\n{raw_alert}"

        payload = {
            "cmdb_ci": self.cmdb_ci,
            "contact_type": self.contact_type,
            "assignment_group": self.assignment_group,
            "category": self.category,
            "subcategory": self.subcategory,
            "u_subcategory_2": self.subcategory_2,
            "short_description": f"{self.short_description_for(device_name)} - {issue_description}"[:160],
            "description": description,
        }
        if correlation_id:
            payload["correlation_id"] = correlation_id
            payload["correlation_display"] = "DNAC-FalseAlertSuppression"
        if self.set_impact_urgency and severity not in (None, ""):
            level = self._severity_to_level(severity)
            payload["impact"] = level
            payload["urgency"] = level

        data = self._request(
            "POST", "/api/now/table/incident",
            json=payload, params={"sysparm_input_display_value": "true"},
        )
        result = data.get("result") or {}
        if not result.get("number"):
            raise ServiceNowError(f"Incident create returned no number: {str(data)[:300]}")
        return result

    @staticmethod
    def _severity_to_level(severity) -> str:
        """DNAC severity 1 (highest) .. 5 -> SNOW impact/urgency 1..3."""
        try:
            sev = int(float(severity))
        except (TypeError, ValueError):
            return "3"
        return "1" if sev <= 1 else ("2" if sev == 2 else "3")

    # ------------------------------------------------------------------
    # Dashboard helper (best effort, never raises)
    # ------------------------------------------------------------------
    def get_incidents_by_numbers(self, incident_numbers: list):
        """Bulk fetch incident display states by INC number (used by the dashboard)."""
        if not self.configured or not incident_numbers:
            return {}
        result = {}
        numbers = [n for n in incident_numbers if n]
        try:
            for i in range(0, len(numbers), 100):
                chunk = numbers[i:i + 100]
                data = self._request("GET", "/api/now/table/incident", params={
                    "sysparm_query": "numberIN" + ",".join(_q(n) for n in chunk),
                    "sysparm_fields": "number,state",
                    "sysparm_display_value": "true",
                    "sysparm_limit": str(len(chunk)),
                })
                for inc in data.get("result", []):
                    result[inc.get("number")] = inc.get("state")
        except ServiceNowError as e:
            logger.error(f"Bulk SNOW query failed: {e}")
        return result
