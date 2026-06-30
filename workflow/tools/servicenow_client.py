import os
import requests
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class ServiceNowClient:
    def __init__(self):
        self.base_url = os.getenv("SNOW_INSTANCE_URL", "").rstrip("/")
        self.username = os.getenv("SNOW_USERNAME", "")
        self.password = os.getenv("SNOW_PASSWORD", "")
        
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    def _build_query(self, device_name: str, active: bool = True, closed_within_days: int = None) -> str:
        # Match user criteria
        query_parts = [
            "cmdb_ci=Network^ORcmdb_ci.name=Network",
            "contact_type=Monitoring",
            "assignment_group.name=Global - CITO Network Services - Dyson",
            "category=Inciden_Infrastructure & Network",
            "subcategory=IT Enabling",
            "u_subcategory_2=Event",
            f"short_descriptionLIKE{device_name}" # Used to match the specific device
        ]
        
        if active:
            query_parts.append("active=true")
        else:
            query_parts.append("active=false")
            if closed_within_days is not None:
                query_parts.append(f"closed_at>=javascript:gs.daysAgoStart({closed_within_days})")
                
        return "^".join(query_parts)
        
    def find_incident(self, device_name: str, active: bool = True, closed_within_days: int = None):
        """Find an incident based on criteria."""
        if not self.base_url:
            return None
            
        sysparm_query = self._build_query(device_name, active, closed_within_days)
        url = f"{self.base_url}/api/now/table/incident?sysparm_query={quote(sysparm_query)}&sysparm_limit=1&sysparm_display_value=true"
        
        try:
            response = requests.get(url, auth=(self.username, self.password), headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json().get("result", [])
            if data:
                return data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to query ServiceNow: {e}")
            return None
            
    def append_comment(self, incident_sys_id: str, comment: str):
        """Add a work note/comment to an existing incident."""
        if not self.base_url:
            return False
            
        url = f"{self.base_url}/api/now/table/incident/{incident_sys_id}"
        payload = {"comments": comment}
        
        try:
            response = requests.put(url, auth=(self.username, self.password), headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to append comment in ServiceNow: {e}")
            return False

    def reopen_incident(self, incident_sys_id: str, comment: str):
        """Reopen an incident (change state to Open) and add a comment."""
        if not self.base_url:
            return False
            
        url = f"{self.base_url}/api/now/table/incident/{incident_sys_id}"
        # SNOW 'Open'/'New' state is typically 1
        payload = {
            "state": "1", 
            "incident_state": "1",
            "comments": comment
        }
        
        try:
            response = requests.put(url, auth=(self.username, self.password), headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to reopen incident in ServiceNow: {e}")
            return False
            
    def create_incident(self, device_name: str, issue_description: str, raw_alert: str):
        """Create a new incident."""
        if not self.base_url:
            return False
            
        url = f"{self.base_url}/api/now/table/incident"
        payload = {
            "cmdb_ci": "Network",
            "contact_type": "Monitoring",
            "assignment_group": "Global - CITO Network Services - Dyson",
            "category": "Inciden_Infrastructure & Network",
            "subcategory": "IT Enabling",
            "u_subcategory_2": "Event",
            "short_description": f"Monitoring Alert: {device_name}",
            "description": f"Issue: {issue_description}\n\nRaw Alert:\n{raw_alert}"
        }
        
        params = {"sysparm_input_display_value": "true"}
        
        try:
            response = requests.post(url, auth=(self.username, self.password), headers=self.headers, json=payload, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get("result", {})
        except Exception as e:
            logger.error(f"Failed to create incident in ServiceNow: {e}")
            return None

    def get_incidents_by_numbers(self, incident_numbers: list):
        """Bulk fetch incident statuses by their INC numbers."""
        if not self.base_url or not incident_numbers:
            return {}
            
        # Create a comma-separated list of INC numbers for the IN operator
        inc_list = ",".join(incident_numbers)
        query = f"numberIN{inc_list}"
        
        url = f"{self.base_url}/api/now/table/incident?sysparm_query={query}&sysparm_fields=number,state&sysparm_display_value=true"
        
        try:
            response = requests.get(url, auth=(self.username, self.password), headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json().get("result", [])
            
            # Map INC number to its display state (e.g., 'In Progress', 'Resolved')
            return {inc.get("number"): inc.get("state") for inc in data}
        except Exception as e:
            logger.error(f"Bulk SNOW query failed: {e}")
            return {}
