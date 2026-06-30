import json
from typing import Any, Dict, Iterable, Optional, Set, List, Union
import re

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------
def parse_json(body: bytes) -> Dict[str, Any]:
    return json.loads(body.decode("utf-8"))

def get_by_path(obj, path: str):
    """
    Supports dot paths like: 'variables.u_machine_id' or 'number'
    """
    cur = obj
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur

def load_mapping(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def flatten_payload(
    payload: Dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
    *,
    exclude_keys: Optional[Set[str]] = None,
    exclude_key_patterns: Optional[List[Union[str, re.Pattern]]] = None,
    drop_empty: bool = False,
) -> Dict[str, Any]:
    """
    Flatten nested JSON-like dict into a flat dict where keys match payload structure.
    
    Examples:
        {"number": "RITM1", "variable_details": {"type": "cname"}}
        -> {"number": "RITM1", "variable_details.type": "cname"}
        
        {"a": [{"b": 1}, {"b": 2}]}
        -> {"a[0].b": 1, "a[1].b": 2}
        
    Parameters
    ----------
    payload : dict
        Input JSON (Python dict).
    parent_key : str
        Used internally for recursion.
    sep : str
        Separator for dict nesting (default ".").
    exclude_keys : set[str] | None
        Exact flattened keys to skip (e.g., {"sys_id", "variable_details.requested_for"}).
    exclude_key_patterns : list[str|Pattern] | None
        Regex patterns to skip keys (matched against flattened key).
        Example: [r"(^|\.)sys_id$", r"(^|\.)sys_updated_on$"]
    drop_empty : bool
        If True, drops values that are None, empty string, empty dict, empty list.
        
    Returns
    -------
    dict
        Flat dict of key -> value.
    """
    exclude_keys = exclude_keys or set()
    
    compiled_patterns: List[re.Pattern] = []
    if exclude_key_patterns:
        for p in exclude_key_patterns:
            compiled_patterns.append(re.compile(p) if isinstance(p, str) else p)
            
    def is_excluded(k: str) -> bool:
        if k in exclude_keys:
            return True
        return any(p.search(k) for p in compiled_patterns)
        
    def is_empty(v: Any) -> bool:
        if v is None:
            return True
        if v == "":
            return True
        if isinstance(v, (dict, list)) and len(v) == 0:
            return True
        return False
        
    out: Dict[str, Any] = {}
    
    def _walk(obj: Any, base: str) -> None:
        # dict
        if isinstance(obj, dict):
            if drop_empty and len(obj) == 0 and base:
                if not is_excluded(base):
                    out[base] = obj
                return
                
            for k, v in obj.items():
                new_key = f"{base}{sep}{k}" if base else str(k)
                _walk(v, new_key)
            return
            
        # list
        if isinstance(obj, list):
            if drop_empty and len(obj) == 0 and base:
                if not is_excluded(base):
                    out[base] = obj
                return
                
            for i, item in enumerate(obj):
                new_key = f"{base}[{i}]"
                _walk(item, new_key)
            return
            
        # primitive (or non-dict/list)
        if base:
            if drop_empty and is_empty(obj):
                return
            if not is_excluded(base):
                out[base] = obj

    _walk(payload, parent_key)
    return out


def map_payload_values(
    catalog: str = "",
    params: Optional[Dict[str, Any]] = None,
    ticket: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    catalog: catalog item description (e.g. 'DNS Records - Add/Update/Delete')
    params: Jenkins parameter dict that will be updated and returned
    ticket: flattened ticket dict (output of flatten_payload), keys like:
        'variable_details.is_this_request_for_a_new'
        'variable_details.is_this_request_for_deleting_dns_record'
    """
    params = params or {}
    ticket = ticket or {}

    if catalog == "DNS Records - Add/Update/Delete":
        # NAME: take host prefix before first dot (if present)
        name_val = params.get("NAME")
        if isinstance(name_val, str) and name_val:
            parts = name_val.split(".", 1)
            params["NAME"] = parts[0]
            if len(parts) > 1:
                params["ZONE_NAME"] = parts[1]

        # RECORD_TYPE mapping example
        if params.get("RECORD_TYPE") == "rec":
            params["RECORD_TYPE"] = "A Record".upper()
            params["HOST_NAME_ALIAS"] = ""
        if params.get("RECORD_TYPE") == "cname":
            params["IPV4ADDRESS"] = ""
            params["RECORD_TYPE"] = "cname".upper()

        # flags are nested under variable_details (flattened keys)
        is_new = ticket.get("variable_details.is_this_request_for_a_new")
        is_delete = ticket.get("variable_details.is_this_request_for_deleting_dns_record")

        if is_new == "yes":
            params["MODE"] = "add"

        # If both yes, DELETE wins (same behavior as your original logic)
        if is_delete == "yes":
            params["MODE"] = "delete"
            
    if catalog == "AWS Access":
        acc_num = params.get("AWSAccountNumbers")
        params["AWSAccountNumbers"] = f"AWS-{acc_num}"

    return params
