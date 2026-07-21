"""
Test: Validate field extraction from a real DNAC webhook payload.

Uses the JSON captured in images/IMG_2730.jpeg + IMG_2731.jpeg as the input
payload, then runs it through every extraction layer in the pipeline to
confirm all fields are fetched correctly.

Also prints the exact DNAC API endpoint + payload for the device-status check.
"""

import json
import sys
import os
import logging

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("test_payload_extraction")

# ---------------------------------------------------------------------------
# The real DNAC payload (transcribed from images/IMG_2730 + IMG_2731)
# ---------------------------------------------------------------------------
DNAC_PAYLOAD = {
    "version": "1.0.0",
    "efInstanceId": "f54eddae-d278-4780-af35-d4759117ee02",
    "instanceId": "39c901fa-b130-499c-836d-017da0f5de7f",
    "eventId": "NETWORK-DEVICES-2-119",
    "namespace": "ASSURANCE",
    "name": None,
    "description": None,
    "type": "NETWORK",
    "category": "ERROR",
    "domain": "Know Your Network",
    "subDomain": "Devices",
    "severity": 2,
    "source": "ndp",
    "timestamp": 1784103979517,
    "details": {
        "Type": "Network Device",
        "Assurance Issue Details": "AP(s) are disconnected from Wireless Controller that are physically connected to Switch UK-MAL-DEV-AS01.dyson.global.corp",
        "Assurance Issue Priority": "P2",
        "Device": "UK-MAL-DEV-AS01.dyson.global.corp",
        "Assurance Issue Name": "AP(s) disconnected from WLC on Switch UK-MAL-DEV-AS01.dyson.global.corp",
        "Assurance Issue Category": "availability",
        "Assurance Issue Status": "active"
    },
    "ciscoDnaEventLink": "https://&lt;DNAC_IP_ADDRESS&gt;/dna/assurance/issueDetails?issueId=39c901fa-b130-499c-836d-017da0f5de7f",
    "note": "To programmatically get more info see here - https://<ip-address>/dna/platform/app/consumer-portal/developer-toolkit/apis?ap",
    "context": None,
    "userId": None,
    "i18n": None,
    "eventHierarchy": None,
    "message": None,
    "messageParams": None,
    "parentInstanceId": None,
    "network": {
        "siteId": "/e76514a4-59f7-48af-8306-f84ddb7baa08/630d33bd-2399-4a4b-955c-f700a69192c7/ecf09391-7969-43a5-93a4-b006-25805562cd92",
        "deviceId": "c10047a1-5464-437b-b1eb-6b4f07b75c58"
    },
    "dnacIP": "",
    "correlationId": "1ab6b782-b40c-4925-93ef-2cf5a4eeb2c0",
    "_source": "dnac-webhook"
}


def separator(title: str):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def main():
    # ==================================================================
    # 1. Show the raw payload
    # ==================================================================
    separator("1. RAW DNAC WEBHOOK PAYLOAD (from images)")
    print(json.dumps(DNAC_PAYLOAD, indent=2))

    # ==================================================================
    # 2. Normalize (flatten) the payload — same as consumer does
    # ==================================================================
    separator("2. NORMALIZED (FLATTENED) PAYLOAD")
    # The consumer module uses relative sys.path hacks that don't work
    # when imported from project root. We add its subdirs to sys.path first.
    consumer_dir = os.path.join(project_root, "consumer")
    for subdir in ["helpers", "config"]:
        path = os.path.join(consumer_dir, subdir)
        if path not in sys.path:
            sys.path.insert(0, path)
    if consumer_dir not in sys.path:
        sys.path.insert(0, consumer_dir)

    from noops_dnac_consumer import normalize_json_payload
    flat = normalize_json_payload(DNAC_PAYLOAD)
    print(json.dumps(flat, indent=2, default=str))

    # ==================================================================
    # 3. Map to Jenkins parameters — same as consumer does
    # ==================================================================
    separator("3. JENKINS PARAMETERS (map_dnac_to_jenkins_params)")
    from jenkins_helpers import map_dnac_to_jenkins_params
    jenkins_params = map_dnac_to_jenkins_params(flat)
    print(json.dumps(jenkins_params, indent=2, default=str))

    # Check for missing/None values
    missing = [k for k, v in jenkins_params.items() if v is None or v == ""]
    if missing:
        print(f"\n[!]  WARNING: The following Jenkins params are None/empty: {missing}")
    else:
        print("\n[OK] All Jenkins parameters populated successfully.")

    # ==================================================================
    # 4. BackdateDetector — same as Agent 1 does
    # ==================================================================
    separator("4. BACKDATE DETECTOR (Agent 1)")
    from workflow.tools.backdate_detector import BackdateDetector
    detector = BackdateDetector(
        threshold_minutes=1440,
        allow_future_skew_seconds=60,
        max_reasonable_age_days=30,
        logger=logger
    )
    # The detector expects the flat alert dict (as run.py passes state["alert"])
    alert_for_detector = {
        "instance_id": flat.get("instanceId"),
        "event_id": flat.get("eventId"),
        "device_id": flat.get("network.deviceId"),
        "device_name": flat.get("details.Device"),
        "raw_timestamp": flat.get("timestamp"),
        "correlation_id": flat.get("correlationId"),
        # Also pass the original nested keys for metadata extraction
        "instanceId": flat.get("instanceId"),
        "eventId": flat.get("eventId"),
        "correlationId": flat.get("correlationId"),
    }
    decision = detector.evaluate(alert_for_detector)
    print(f"  is_backdated    : {decision.is_backdated}")
    print(f"  reason          : {decision.reason}")
    print(f"  explanation     : {decision.explanation}")
    print(f"  event_ts_ms     : {decision.event_timestamp_ms}")
    print(f"  ingestion_ts_ms : {decision.ingestion_timestamp_ms}")
    print(f"  skew_ms         : {decision.skew_ms}")
    print(f"  threshold_ms    : {decision.threshold_ms}")
    print(f"  instance_id     : {decision.instance_id}")
    print(f"  event_id        : {decision.event_id}")
    print(f"  device_id       : {decision.device_id}")
    print(f"  device_name     : {decision.device_name}")
    print(f"  correlation_id  : {decision.correlation_id}")

    # ==================================================================
    # 5. DNAC Device Status API — endpoint + payload
    # ==================================================================
    separator("5. DNAC DEVICE STATUS CHECK — ENDPOINT & PAYLOAD")

    import yaml
    config_path = os.path.join(project_root, "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    dnac_base_url = config["dnac"]["base_url"].rstrip("/")
    instance_id = DNAC_PAYLOAD["instanceId"]

    endpoint_url = f"{dnac_base_url}/dna/intent/api/v1/issues/{instance_id}"

    print("This is the DNAC API call made by DNACClient.get_issue_status():\n")
    print(f"  Method  : GET")
    print(f"  URL     : {endpoint_url}")
    print(f"  Headers :")
    print(f"    x-auth-token : <obtained from POST {dnac_base_url}/dna/system/api/v1/auth/token>")
    print(f"    Content-Type : application/json")
    print(f"    Accept       : application/json")
    print(f"  Body    : (none — GET request)")
    print()
    print("  Expected Response (example):")
    expected_response = {
        "response": {
            "issueId": instance_id,
            "issueStatus": "ACTIVE",   # or "RESOLVED", "IGNORED", "CLEARED"
            "issueName": DNAC_PAYLOAD["details"]["Assurance Issue Name"],
            "issuePriority": DNAC_PAYLOAD["details"]["Assurance Issue Priority"],
            "issueCategory": DNAC_PAYLOAD["details"]["Assurance Issue Category"],
            "deviceId": DNAC_PAYLOAD["network"]["deviceId"],
        }
    }
    print(f"  {json.dumps(expected_response, indent=4)}")

    # Also show the auth endpoint
    print()
    separator("5b. DNAC AUTHENTICATION ENDPOINT (called first)")
    auth_url = f"{dnac_base_url}/dna/system/api/v1/auth/token"
    print(f"  Method  : POST")
    print(f"  URL     : {auth_url}")
    print(f"  Auth    : HTTP Basic Auth (DNAC_USERNAME / DNAC_PASSWORD from .env)")
    print(f"  Body    : (none)")
    print(f"  Response: {{ \"Token\": \"<jwt-token>\" }}")

    # ==================================================================
    # 6. Full field extraction summary
    # ==================================================================
    separator("6. FIELD EXTRACTION SUMMARY")
    fields = {
        "instanceId (issue ID)":        flat.get("instanceId"),
        "eventId":                      flat.get("eventId"),
        "category":                     flat.get("category"),
        "severity":                     flat.get("severity"),
        "timestamp (epoch ms)":         flat.get("timestamp"),
        "source":                       flat.get("_source") or flat.get("source"),
        "correlationId":                flat.get("correlationId"),
        "device (name)":                flat.get("details.Device"),
        "deviceId":                     flat.get("network.deviceId"),
        "siteId":                       flat.get("network.siteId"),
        "issue status":                 flat.get("details.Assurance_Issue_Status"),
        "issue name":                   flat.get("details.Assurance_Issue_Name"),
        "issue details":                flat.get("details.Assurance_Issue_Details"),
        "issue priority":               flat.get("details.Assurance_Issue_Priority"),
        "issue category":               flat.get("details.Assurance_Issue_Category"),
        "domain":                       flat.get("domain"),
        "subDomain":                    flat.get("subDomain"),
        "namespace":                    flat.get("namespace"),
        "type":                         flat.get("type"),
        "version":                      flat.get("version"),
        "efInstanceId":                 flat.get("efInstanceId"),
    }

    max_key_len = max(len(k) for k in fields)
    all_ok = True
    for key, val in fields.items():
        status = "[OK]" if val is not None else "[MISSING] MISSING"
        if val is None:
            all_ok = False
        print(f"  {key:<{max_key_len}} : {status}  {val}")

    print()
    if all_ok:
        print("[OK] All fields extracted successfully from the DNAC payload.")
    else:
        print("[!]  Some fields are missing — see [MISSING] markers above.")


if __name__ == "__main__":
    main()
