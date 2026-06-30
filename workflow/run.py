import os
import sys
import argparse
import json
import logging
from datetime import datetime, timezone
from contextlib import contextmanager, redirect_stdout, redirect_stderr

# =======================
# Path setup
# =======================
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from workflow.graph import build_graph  # avoid wildcard import in prod

LOG = logging.getLogger("run")

# Jenkins-friendly exit codes
EXIT_CODES = {
    "success": 0,
    "partial_failure": 2,    # treat as UNSTABLE in pipeline if you want
    "failed": 1,
    "unknown": 1,
    "config_error": 3,
}

def utc_now() -> str:
    """Timezone-aware UTC timestamp (no deprecation warning)."""
    return datetime.now(timezone.utc).isoformat()

def write_json_file(path: str, payload: dict) -> None:
    """Write JSON file for Jenkins artifacts. Never raises."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        LOG.error("Failed to write file %s: %s", path, e)

def compute_overall_from_results(results: dict) -> str:
    """Fallback overall status if reporter didn't set overall_status."""
    statuses = [v.get("status") for v in (results or {}).values()]

    if any(s == "failed" for s in statuses):
        if any(s == "success" for s in statuses):
            return "partial_failure"
        return "failed"
        
    if statuses and all(s in ("success", "skipped") for s in statuses):
        return "success"
        
    return "unknown"

def configure_silent_runtime():
    """
    Silence noisy library logs (transformers/torch/etc.) so Jenkins console stays clean.
    NOTE: This only controls logging; print() noise is handled by redirect below.
    """
    # Default to WARNING to reduce noise; override via --log-level if needed
    # run.py will still print its own summary.
    for name in [
        "transformers",
        "datasets",
        "torch",
        "urllib3",
        "botocore",
        "s3transfer",
        "huggingface_hub",
        "noops-incident-consumer",
    ]:
        logging.getLogger(name).setLevel(logging.ERROR)
        
    # HuggingFace knobs (progress bars etc.)
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

@contextmanager
def redirect_all_output(to_path: str):
    """
    Redirect *all* stdout + stderr to a log file.
    This ensures Jenkins console only shows run.py prints outside this context.
    """
    os.makedirs(os.path.dirname(to_path) or ".", exist_ok=True)
    with open(to_path, "a", encoding="utf-8") as f:
        with redirect_stdout(f), redirect_stderr(f):
            yield

def build_summary(final_state: dict, stage: str, runtime_error: str = None) -> dict:
    overall = (final_state or {}).get("overall_status", "unknown")
    results = (final_state or {}).get("results", {})
    errors = (final_state or {}).get("errors", [])
    
    # Ensure overall_status is never missing/unknown if results exist
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

def main() -> int:
    parser = argparse.ArgumentParser(description="Run Incident Triage flow (Jenkins-clean console)")
    
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
    
    # Jenkins outputs
    parser.add_argument("--status-file", default="status.json", help="write summary JSON to this file")
    parser.add_argument("--run-log", default="run.log", help="Redirect all internal output to this log file")
    
    # Logging
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "WARNING"),
                        help="Log level for run.py (default WARNING to reduce noise)")
                        
    # If set, run.py will print only the final JSON summary (default True)
    parser.add_argument("--quiet-console", default=os.getenv("QUIET_CONSOLE", "1"),
                        help="1 to print only JSON summary to console (default 1)")
                        
    args = parser.parse_args()
    
    from workflow.utils.logger import configure_logging
    configure_logging(level=getattr(logging, args.log_level.upper(), logging.WARNING))
    
    configure_silent_runtime()
    
    quiet_console = str(args.quiet_console).strip() not in ("0", "false", "False", "")
    
    # Build initial state
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
        }
    }
    
    # Run graph with ALL internal outputs redirected to run.log
    final_state = None
    try:
        graph = build_graph()
        
        with redirect_all_output(args.run_log):
            final_state = graph.invoke(initial_state)
            
        summary = build_summary(final_state, stage="completed")
        
        # Console output: ONLY run.py print statements (JSON summary)
        print(json.dumps(summary, indent=2))
        
        # Write status.json for Jenkins artifact
        write_json_file(args.status_file, summary)
        
        overall = summary.get("overall_status", "unknown")
        return EXIT_CODES.get(overall, 1)
        
    except Exception as e:
        summary = build_summary(final_state or {}, stage="runtime_error", runtime_error=str(e))
        
        # Always print JSON summary so Jenkins gets something useful
        print(json.dumps(summary, indent=2))
        write_json_file(args.status_file, summary)
        
        # Also append the exception to run.log for debugging
        try:
            with open(args.run_log, "a", encoding="utf-8") as f:
                f.write("\n[RUNTIME_ERROR] " + str(e) + "\n")
        except Exception:
            pass
            
        return EXIT_CODES["failed"]

if __name__ == "__main__":
    sys.exit(main())
