import os
import sys
import argparse
import json
import logging
from datetime import datetime, timezone
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from typing import Union, Optional

# =======================
# Path setup
# =======================
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from workflow.nodes.node_agent_4_servicenow import agent_4_servicenow
from workflow.nodes.node_email_notifier import email_notifier
from workflow.nodes.node_reporter import reporter

LOG = logging.getLogger("run_delayed")

# Jenkins-friendly exit codes
EXIT_CODES = {
    "success": 0,
    "partial_failure": 2,    
    "failed": 1,
    "unknown": 1,
    "config_error": 3,
}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_json_file(path: str, payload: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        LOG.error("Failed to write file %s: %s", path, e)

def compute_overall_from_results(results: dict) -> str:
    statuses = [v.get("status") for v in (results or {}).values()]

    if any(s == "failed" for s in statuses):
        if any(s == "success" for s in statuses):
            return "partial_failure"
        return "failed"
        
    if statuses and all(s in ("success", "skipped") for s in statuses):
        return "success"
        
    return "unknown"

def configure_silent_runtime():
    for name in [
        "transformers", "datasets", "torch", "urllib3",
        "botocore", "s3transfer", "huggingface_hub", "noops-incident-consumer",
    ]:
        logging.getLogger(name).setLevel(logging.ERROR)
        
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

@contextmanager
def redirect_all_output(to_path: str):
    os.makedirs(os.path.dirname(to_path) or ".", exist_ok=True)
    with open(to_path, "a", encoding="utf-8") as f:
        with redirect_stdout(f), redirect_stderr(f):
            yield

def build_summary(final_state: dict, stage: str, runtime_error: str = None) -> dict:
    overall = (final_state or {}).get("overall_status", "unknown")
    results = (final_state or {}).get("results", {})
    errors = (final_state or {}).get("errors", [])
    
    if (not overall) or overall == "unknown":
        fallback = compute_overall_from_results(results)
        overall = fallback
        if final_state is not None:
            final_state["overall_status"] = overall
            
    return {
        "timestamp": utc_now(),
        "stage": stage,
        "overall_status": overall if stage == "completed" else "failed",
        "results": results,
        "errors": errors,
        "runtime_error": runtime_error,
    }

def check_dnac_status(
    instance_id: str = None,
    device_id: str = None,
    device_name: str = None,
    issue_name: str = None,
    issue_details: str = None,
    event_id: str = None
) -> Union[bool, str]:
    """
    Check DNAC to see if the alert is still active.
    Returns:
      - True if still active in DNAC (primary check or fallback active match)
      - False if resolved in DNAC (primary check or fallback resolved match)
      - "Uncertain" if alert cannot be found in active or resolved lists
    """
    import yaml
    try:
        from app.dnac_client import DNACClient
    except ImportError:
        # Fallback if run_delayed.py is called from a different working directory
        sys.path.insert(0, os.path.dirname(project_root))
        from app.dnac_client import DNACClient
    
    # Load config.yaml
    config_path = os.path.join(project_root, "config.yaml")
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        LOG.error(f"Failed to load config.yaml for DNAC check: {e}")
        return "Uncertain"
        
    try:
        dnac_config = config.get("dnac", {})
        client = DNACClient(dnac_config)

        # 1. Primary check using instance_id
        if instance_id:
            status = client.get_issue_status(instance_id)
            LOG.info(f"DNAC primary status check result for instance_id={instance_id}: status={status}")
            if status != "NOT_FOUND":
                if status.upper() in ["RESOLVED", "IGNORED", "CLEARED", "DELETED"]:
                    return False
                else:
                    return True
            LOG.info(f"instance_id={instance_id} returned NOT_FOUND (404). Triggering device fallback check.")

        # Helper function for description matching
        def is_match(issue: dict) -> bool:
            target_texts = [str(t).strip().lower() for t in [issue_name, issue_details, event_id] if t]
            if not target_texts:
                return False
            issue_texts = [
                str(issue.get(k, "")).strip().lower()
                for k in ["name", "issueName", "description", "issueDescription", "issueDetails", "title", "summary", "eventId"]
                if issue.get(k)
            ]
            for target in target_texts:
                for itext in issue_texts:
                    if target in itext or itext in target:
                        return True
            return False

        # 2. Fallback Step A: Check active device issues
        LOG.info(f"Checking active issues for device_id={device_id}, device_name={device_name}")
        active_issues = client.get_device_issues(device_id=device_id, device_name=device_name, issue_status="ACTIVE")
        for issue in active_issues:
            iss_status = str(issue.get("issueStatus", issue.get("status", "ACTIVE"))).upper()
            if iss_status not in ["RESOLVED", "IGNORED", "CLEARED", "DELETED"]:
                if is_match(issue):
                    LOG.info(f"Fallback check: Found matching active issue on device {device_id}/{device_name}")
                    return True

        # 3. Fallback Step B: Check resolved device issues
        LOG.info(f"Checking resolved issues for device_id={device_id}, device_name={device_name}")
        resolved_issues = client.get_device_issues(device_id=device_id, device_name=device_name, issue_status="RESOLVED")
        for issue in resolved_issues:
            iss_status = str(issue.get("issueStatus", issue.get("status", "RESOLVED"))).upper()
            if iss_status in ["RESOLVED", "IGNORED", "CLEARED", "DELETED"]:
                if is_match(issue):
                    LOG.info(f"Fallback check: Found matching resolved issue on device {device_id}/{device_name}")
                    return False

        # 4. Fallback Step C: If not found in active or resolved list -> Uncertain
        LOG.warning(f"Fallback check: Issue not found in active or resolved issues for device {device_id}/{device_name}. Marking as Uncertain.")
        return "Uncertain"

    except Exception as e:
        LOG.error(f"DNAC status check failed: {e}. Defaulting to Uncertain.")
        return "Uncertain"

def main() -> int:
    parser = argparse.ArgumentParser(description="Run Delayed Incident Triage flow")
    
    parser.add_argument("--instance_id", required=False, help="Alert instance id")
    parser.add_argument("--event_id", required=True, help="Alert event id")
    parser.add_argument("--device_id", required=True, help="Network device id")
    parser.add_argument("--device_name", required=True, help="Network device name")
    parser.add_argument("--severity", required=False, help="Alert severity")
    parser.add_argument("--category", required=False, help="Alert category")
    parser.add_argument("--status", required=False, help="Alert status")
    parser.add_argument("--raw_timestamp", required=False, help="Alert timestamp")
    parser.add_argument("--correlation_id", required=False, help="Alert correlation")
    parser.add_argument("--source", required=False, help="Alert source")
    parser.add_argument("--issue_name", required=False, help="Alert issue name")
    parser.add_argument("--issue_details", required=False, help="Alert details")
    
    parser.add_argument("--status-file", default="status.json", help="write summary JSON to this file")
    parser.add_argument("--run-log", default="run.log", help="Redirect all internal output to this log file")
    
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "WARNING"),
                        help="Log level for run.py")
    parser.add_argument("--quiet-console", default=os.getenv("QUIET_CONSOLE", "1"))
                        
    # Additional flags that might be passed from Jenkins job, e.g. IS_DELAYED
    parser.add_argument("--is-delayed", action="store_true", help="Flag indicating this is a delayed alert check")
                        
    args, unknown = parser.parse_known_args()
    
    from workflow.utils.logger import configure_logging
    configure_logging(level=getattr(logging, args.log_level.upper(), logging.WARNING))
    
    configure_silent_runtime()
    
    initial_state = {
        "alert": {
            "instance_id": args.instance_id,
            "event_id": args.event_id,
            "device_id": args.device_id,
            "device_name": args.device_name,
            "severity": args.severity,
            "category": args.category,
            "status": args.status,
            "raw_timestamp": args.raw_timestamp,
            "correlation_id": args.correlation_id,
            "source": args.source,
            "issue_name": args.issue_name,
            "issue_details": args.issue_details
        },
        "results": {}
    }
    
    final_state = None
    try:
        with redirect_all_output(args.run_log):
            status = check_dnac_status(
                instance_id=args.instance_id,
                device_id=args.device_id,
                device_name=args.device_name,
                issue_name=args.issue_name,
                issue_details=args.issue_details,
                event_id=args.event_id
            )
            if status is True or status == "ACTIVE":
                LOG.warning(f"Alert {args.event_id} STILL ACTIVE in DNAC. Forcing escalation.")
                initial_state["results"]["agent_2"] = {
                    "data": {"predicted_category": "Non-Auto Resolving"}
                }
                agent4_result = agent_4_servicenow(initial_state)
                initial_state["results"]["agent_4"] = agent4_result
            elif status == "Uncertain":
                LOG.warning(f"Alert {args.event_id} status UNCERTAIN in DNAC. Forcing escalation to be safe.")
                initial_state["results"]["agent_2"] = {
                    "data": {"predicted_category": "Uncertain"}
                }
                agent4_result = agent_4_servicenow(initial_state)
                initial_state["results"]["agent_4"] = agent4_result
            else:
                # Alert resolved
                LOG.info(f"Alert {args.event_id} is resolved in DNAC. No ServiceNow ticket required.")
                initial_state["results"]["delayed_check"] = {"status": "resolved"}
                
            # Send Email and Report
            initial_state = email_notifier(initial_state)
            final_state = reporter(initial_state)
            
        summary = build_summary(final_state, stage="completed")
        print(json.dumps(summary, indent=2))
        write_json_file(args.status_file, summary)
        
        overall = summary.get("overall_status", "unknown")
        return EXIT_CODES.get(overall, 1)
        
    except Exception as e:
        summary = build_summary(final_state or {}, stage="runtime_error", runtime_error=str(e))
        print(json.dumps(summary, indent=2))
        write_json_file(args.status_file, summary)
        try:
            with open(args.run_log, "a", encoding="utf-8") as f:
                f.write("\n[RUNTIME_ERROR] " + str(e) + "\n")
        except Exception:
            pass
        return EXIT_CODES["failed"]

if __name__ == "__main__":
    sys.exit(main())
