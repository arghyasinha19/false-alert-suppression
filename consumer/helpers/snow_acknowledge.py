import base64
import requests
from typing import Optional, Dict, Any

class ServiceNowClient:
    """
    Simple ServiceNow Table API client for updating comments/work_notes via PATCH.
    Uses Basic Auth header (username:password). For production, prefer OAuth tokens.
    Table API supports CRUD operations on tables via /api/now/table/{table}/{sys_id}.
    """
    
    def __init__(self, instance_url: str, username: str, password: str, timeout: int = 30):
        self.instance_url = instance_url.rstrip("/")
        self.timeout = timeout
        
        # Basic Auth header
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
        self.headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
    def patch_record(self, table: str, sys_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        PATCH /api/now/table/{table}/{sys_id}
        """
        url = f"{self.instance_url}/api/now/table/{table}/{sys_id}"
        resp = requests.patch(url, headers=self.headers, json=payload, timeout=self.timeout)
        
        # Raise helpful error details
        if not resp.ok:
            raise RuntimeError(
                f"ServiceNow PATCH failed: {resp.status_code} {resp.reason} | {resp.text}"
            )
            
        return resp.json()
        
def update_comment(
    sn: ServiceNowClient,
    table: str,
    sys_id: str,
    message: str,
    *,
    customer_visible: bool = True,
    internal_note: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update ServiceNow journal fields after denial:
      - customer_visible=True  -> writes to 'comments' (Additional Comments)
      - internal_note provided -> writes to 'work_notes' (Work Notes)
      
    Writing to comments/work_notes is done by updating the parent record's fields
    via Table API PATCH.
    """
    payload = {}
    
    if customer_visible:
        payload["comments"] = message
    else:
        # If you want ONLY internal, use work_notes
        payload["work_notes"] = message
        
    if internal_note:
        payload["work_notes"] = internal_note
        
    return sn.patch_record(table=table, sys_id=sys_id, payload=payload)
