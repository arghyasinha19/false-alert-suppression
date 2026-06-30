import time
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

import requests

@dataclass
class JenkinsConfig:
    base_url: str                 # e.g. "https://jenkins.company.com/"
    username: str                 # e.g. "svc-jenkins"
    api_token: str                # API token for the user
    verify_tls: bool = False      # set False only if you must (not recommended)
    timeout_sec: int = 30         # request timeout


class JenkinsTriggerError(Exception):
    pass


class JenkinsHelper:
    """
    Production-grade helper to trigger a parameterized Jenkins job remotely.
    """
    def __init__(self, config: JenkinsConfig, logger: Optional[logging.Logger] = None):
        self.cfg = config
        self.log = logger or logging.getLogger("jenkins.helper")
        
        self.session = requests.Session()
        self.session.auth = (self.cfg.username, self.cfg.api_token)
        self.session.verify = self.cfg.verify_tls
        self.session.headers.update({
            "User-Agent": "dnac-automation/jenkins-helper",
            "Accept": "application/json",
        })

    # -------------------------------------------------------------------------
    # Public method
    # -------------------------------------------------------------------------
    def trigger_parameterized_job(
        self,
        job_path: str,
        params: Dict[str, Any],
        *,
        token: Optional[str] = None,
        cause: Optional[str] = None,
        retries: int = 3,
        backoff_sec: float = 1.0
    ) -> Dict[str, Any]:
        """
        Trigger a parameterized job:
        POST {base_url}/{job_path}/buildWithParameters
        
        job_path examples:
          - "job/MyJob"
          - "job/Folder/job/MyJob"
          - full URL also supported
          
        params:
          dict of key/values for Jenkins parameters. Values will be coerced to strings.
          
        token:
          If your Jenkins job uses "Build Token Root Plugin" or job token, pass it here.
          (Commonly not needed when using user+API token auth.)
          
        cause:
          Adds a 'cause' message (visible in Jenkins build cause in some setups).
        """
        
        if not isinstance(params, dict) or not params:
            raise ValueError("params must be a non-empty dict")
            
        # Convert param values to strings (Jenkins build parameters are typically strings)
        safe_params = {str(k): self._to_param_value(v) for k, v in params.items()}
        
        # Optional extras
        if token:
            safe_params["token"] = token
        if cause:
            safe_params["cause"] = cause
            
        # URL resolve
        build_url = self._build_with_params_url(job_path)
        
        # Add crumb if CSRF enabled
        headers = {}
        crumb_header = self._get_crumb_header()
        if crumb_header:
            headers.update(crumb_header)
            
        # Attempt with retries
        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                self.log.info(
                    "Triggering Jenkins job (attempt %s/%s): job_path=%s params_keys=%s",
                    attempt, retries, job_path, list(safe_params.keys())
                )
                
                resp = self.session.post(
                    build_url,
                    data=safe_params,      # Jenkins expects form-encoded
                    headers=headers,
                    timeout=self.cfg.timeout_sec
                )
                
                # 201 Created is common, 200 OK can happen based on plugins
                if resp.status_code not in (200, 201, 202):
                    raise JenkinsTriggerError(
                        f"Jenkins trigger failed: status={resp.status_code} body={resp.text[:500]}"
                    )
                    
                queue_url = resp.headers.get("Location") # Jenkins returns queue item URL here
                result = {
                    "ok": True,
                    "status_code": resp.status_code,
                    "queue_url": queue_url,
                    "job_trigger_url": build_url,
                    "sent_params_keys": list(safe_params.keys())
                }
                
                # Optionally parse queue id
                if queue_url:
                    qid = self._extract_queue_id(queue_url)
                    if qid is not None:
                        result["queue_id"] = qid
                        
                self.log.info("Jenkins job triggered successfully: queue_url=%s", queue_url)
                return result
                
            except Exception as e:
                last_exc = e
                self.log.warning("Trigger attempt %s failed: %s", attempt, str(e))
                if attempt < retries:
                    sleep_for = backoff_sec * (2 ** (attempt - 1))
                    time.sleep(sleep_for)
                    
        raise JenkinsTriggerError(f"All retries failed while triggering Jenkins job: {last_exc}")

    # -------------------------------------------------------------------------
    # Optional: poll queue until build starts
    # -------------------------------------------------------------------------
    def wait_for_build_number(
        self,
        queue_url: str,
        *,
        poll_interval_sec: float = 2.0,
        timeout_sec: int = 120
    ) -> Dict[str, Any]:
        """
        Polls the Jenkins queue item until it gets an executable/build number.
        Returns: {build_number, build_url, job_url}
        """
        if not queue_url:
            raise ValueError("queue_url is required")
            
        headers = {}
        crumb_header = self._get_crumb_header()
        if crumb_header:
            headers.update(crumb_header)
            
        api_url = queue_url.rstrip("/") + "/api/json"
        
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            resp = self.session.get(api_url, headers=headers, timeout=self.cfg.timeout_sec)
            if resp.status_code != 200:
                raise JenkinsTriggerError(f"Queue poll failed: status={resp.status_code} body={resp.text[:500]}")
                
            data = resp.json()
            # When job starts, 'executable' appears
            if data.get("executable") and data["executable"].get("number"):
                build_number = data["executable"]["number"]
                build_url = data["executable"].get("url")
                job_url = data.get("task", {}).get("url")
                return {
                    "ok": True,
                    "build_number": build_number,
                    "build_url": build_url,
                    "job_url": job_url
                }
                
            if data.get("cancelled"):
                raise JenkinsTriggerError("Queue item was cancelled before execution")
                
            time.sleep(poll_interval_sec)
            
        raise JenkinsTriggerError(f"Timed out waiting for build to start (queue_url={queue_url})")

    # -------------------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------------------
    def _build_with_params_url(self, job_path: str) -> str:
        # Accept full URL too
        if job_path.startswith("http://") or job_path.startswith("https://"):
            base = job_path.rstrip("/") + "/"
        else:
            base = urljoin(self.cfg.base_url.rstrip("/") + "/", job_path.strip("/").rstrip("/") + "/")
        return urljoin(base, "buildWithParameters")
        
    def _get_crumb_header(self) -> Optional[Dict[str, str]]:
        """
        If CSRF crumb issuer is enabled, Jenkins requires a crumb header.
        Endpoint: /crumbIssuer/api/json
        If disabled, it might return 404.
        """
        crumb_url = urljoin(self.cfg.base_url.rstrip("/") + "/", "crumbIssuer/api/json")
        try:
            resp = self.session.get(crumb_url, timeout=self.cfg.timeout_sec)
            if resp.status_code == 404:
                return None # crumb issuer disabled
            if resp.status_code != 200:
                # Some Jenkins setups block crumb endpoint; don't fail hard
                self.log.debug("Crumb issuer response non-200: %s", resp.status_code)
                return None
                
            data = resp.json()
            field = data.get("crumbRequestField")
            crumb = data.get("crumb")
            if field and crumb:
                return {field: crumb}
        except Exception:
            # Don't block triggering if crumb fetch fails; user might have CSRF disabled
            return None
            
        return None
        
    def _to_param_value(self, v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        return str(v)
        
    def _extract_queue_id(self, queue_url: str) -> Optional[int]:
        # Typical queue url: https://jenkins/queue/item/123/
        parts = queue_url.rstrip("/").split("/")
        if parts and parts[-1].isdigit():
            return int(parts[-1])
        return None
        
def map_dnac_to_jenkins_params(flat: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "INSTANCE_ID": flat.get("instanceId"),
        "EVENT_ID": flat.get("eventId"),
        "DEVICE_ID": flat.get("network.deviceId"),
        "DEVICE_NAME": flat.get("details.Device"),
        "SEVERITY": flat.get("severity"),
        "CATEGORY": flat.get("category"),
        "STATUS": flat.get("details.Assurance_Issue_Status"),
        "RAW_TIMESTAMP": flat.get("timestamp"),
        "CORRELATION_ID": flat.get("correlationId"),
        "SOURCE": flat.get("_source"),
        "ISSUE_NAME": flat.get("details.Assurance_Issue_Name"),
        "ISSUE_DETAILS": flat.get("details.Assurance_Issue_Details"),
    }
