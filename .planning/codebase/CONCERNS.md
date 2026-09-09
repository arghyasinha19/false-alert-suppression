# Codebase Concerns

**Analysis Date:** 2026-09-09

## Tech Debt

**Duplicate Utility Hierarchies:**
- Issue: Utility and helper code is duplicated between `consumer/helpers/` (e.g. `logger.py`, `rabbitmq_helpers.py`) and `workflow/utils/` + `workflow/tools/` (e.g. `logger.py`, `message_broker.py`).
- Files: `consumer/helpers/logger.py`, `workflow/utils/logger.py`, `consumer/helpers/rabbitmq_helpers.py`, `workflow/tools/message_broker.py`.
- Impact: Inconsistent logging formatting and dual maintenance overhead when updating connection logic or retry policies.
- Fix approach: Consolidate shared utilities into a unified package (e.g., `common/` or `core/`) shared across `app`, `consumer`, and `workflow`.

**Inconsistent Runtime Path Injections:**
- Issue: Almost every script manually modifies `sys.path` with `sys.path.insert(0, ...)` or `sys.path.append(...)`. In `consumer/noops_dnac_consumer.py:23`, it attempts to append a non-existent `mapping/` folder.
- Files: `consumer/noops_dnac_consumer.py`, `consumer/consumer-delay-queue.py`, `workflow/run.py`, `workflow/run_delayed.py`, `dashboard/api.py`.
- Impact: Fragile imports that break if files are moved; confusing IDE resolution and static analysis warnings.
- Fix approach: Package the solution as an installable Python package (`pip install -e .` with `pyproject.toml`) and eliminate manual `sys.path` modifications.

**Fragmented Root Test Scripts:**
- Issue: Test files are scattered in the project root (`test_dnac_fallback.py`, `test_ensemble.py`, `test_payload_extraction.py`, `test_rmq.py`, `check_api.py`, `check_mongo.py`) rather than organized under a standard `tests/` directory.
- Files: `test_*.py`, `check_*.py`.
- Impact: Discovery issues with standard CI runners (`pytest`); clutter in top-level directory.
- Fix approach: Migrate test files to `tests/unit/` and `tests/integration/` with a shared `conftest.py`.

## Known Bugs & Fragile Areas

**Synchronous Jenkins Wait Blocking AMQP Consumer Heartbeat:**
- Symptoms: If Jenkins is busy or slow, `consumer/noops_dnac_consumer.py` blocks for up to 120 seconds in `jh.wait_for_build_number(trigger_result["queue_url"], timeout_sec=120)`.
- Files: `consumer/noops_dnac_consumer.py:223`.
- Trigger: Network latency or queue buildup in Jenkins.
- Impact: The Pika AMQP connection misses its 60-second heartbeat interval, causing RabbitMQ to force-close the channel (`AMQPConnectionError`), resulting in duplicate message deliveries and reconnection loops.
- Workaround/Fix: Fire-and-forget job triggering or run consumer with async Pika / Celery / Task queue; decouple Jenkins queue polling from the AMQP message acknowledgement loop.

**Heuristic Alert Description Fallback Chain:**
- Symptoms: If DNAC alters payload keys, classification falls back to empty strings and skips Agent 2.
- Files: `workflow/nodes/node_agent_2.py:75-84`.
- Trigger: Cisco DNAC firmware updates changing key naming from `Assurance Issue Details` or `details.description`.
- Workaround/Fix: Formalize a Pydantic incoming alert schema with explicit field aliases and validation errors.

## Security Considerations

**Disabled SSL Verification by Default:**
- Risk: Potential Man-In-The-Middle (MITM) vulnerabilities when transmitting credentials and payloads over corporate networks.
- Files: `config.yaml:3` (`verify_ssl: false`), `consumer/helpers/jenkins_helpers.py:53` (`verify_tls=False`), `app/main.py:42`, `dashboard/chat_agent.py:36` (`urllib3.disable_warnings`).
- Current mitigation: Internal network boundary assumptions (RFC 1918 private IPs).
- Recommendations: Support enterprise root CA certificate bundles (`REQUESTS_CA_BUNDLE`) and make TLS verification mandatory in staging/production environments.

**Local `.env` Credential Exposure:**
- Risk: Plaintext service credentials for Cisco DNAC, RabbitMQ, ServiceNow, and Google Gemini stored on disk.
- Files: `.env`, `config.yaml`.
- Current mitigation: `.gitignore` contains `.env`.
- Recommendations: Integrate with enterprise vault services (e.g. HashiCorp Vault, AWS Secrets Manager, or CyberArk) or pass secrets via Jenkins/Kubernetes secret managers.

**Hardcoded Appliance IPs:**
- Risk: Internal network topology and IP addresses (`10.48.200.53`, `10.208.130.50`, `10.64.1.189`) committed directly to `config.yaml`.
- Files: `config.yaml`.
- Recommendations: Parameterize hostnames via DNS or environment variable placeholders (`${DNAC_HOST}`).

## Performance Bottlenecks

**Sequential Real-Time ServiceNow Incident Enrichment in Dashboard:**
- Problem: The dashboard `/api/alerts` endpoint calls ServiceNow on each load to fetch live incident statuses.
- Files: `dashboard/api.py:100`.
- Cause: Synchronous or iterative queries against ServiceNow REST API when viewing large lists of alerts.
- Improvement path: Cache ServiceNow statuses in MongoDB asynchronously via a background worker rather than executing external REST calls in the HTTP request-response path.

**Cold Start Latency for Deep Learning Model:**
- Problem: If `ml_model.joblib` has confidence < 0.85, the pipeline falls back to DistilBERT, which takes several seconds to initialize on cold workers.
- Files: `workflow/nodes/node_agent_2.py:120`, `workflow/classifier/model.py`.
- Cause: Model weight loading and tokenizer initialization.
- Improvement path: Keep worker processes warm or prioritize ONNX Runtime optimization with pre-warmed inference sessions.

## Scaling Limits

**One Jenkins Pipeline Run Per Alert:**
- Current capacity: Handles tens of alerts per hour.
- Limit: During network events (e.g. switch stack restart, edge router flap), DNAC can emit thousands of alerts in minutes ("alert storms").
- Bottleneck: Spawning one Jenkins pipeline execution per alert will saturate Jenkins executors, exhaust queue slots, and cause minutes-long processing lag.
- Scaling path: Introduce batch ingestion in `consumer/noops_dnac_consumer.py` or run the LangGraph workflow directly in containerized worker pods (Kubernetes / Celery) rather than dispatching individual Jenkins jobs.

## Dependencies at Risk

**React 19 & Third-Party Compatibility:**
- Package: `react@19.2.7` in `dashboard/package.json`.
- Risk: Bleeding-edge React version with peer dependency friction on older component libraries.
- Impact: Potential build warnings or compatibility issues with charting extensions.
- Migration plan: Pinned strictly to `19.2.7` and tested against `recharts@3.9.0`.

## Missing Critical Features

**Automated Dead-Letter Queue (DLQ) Reprocessing UI:**
- Problem: When alerts fail max retries (3) in `consumer/noops_dnac_consumer.py`, they are routed to `dnac.alerts.dlq`. There is currently no UI or automated tool to inspect, edit, and replay dead-lettered alerts.
- Blocks: Rapid incident remediation for malformed payloads or transient infrastructure outages.

**Automated Model Retraining Feedback Loop:**
- Problem: Operator corrections on false alert predictions are saved to MongoDB, but there is no scheduled pipeline to retrain `models/ml_model.joblib` or update DistilBERT weights.
- Blocks: Continuous learning from operator feedback.

## Test Coverage Gaps

**LangGraph Pipeline Integration Tests:**
- What's not tested: Complete end-to-end execution of `workflow/graph.py` with mock alert payloads verifying that `agent_1` -> `agent_2` -> `agent_3` -> `agent_4` transitions and state accumulation occur as expected.
- Files: `workflow/graph.py`, `workflow/state.py`.
- Risk: Logic regression in conditional edges or TypedDict keys causing silent drops.
- Priority: High.

**Dashboard Backend & Chat Agent Automation:**
- What's not tested: Automated API tests for `dashboard/api.py` endpoints (`/api/alerts`, `/api/devices`, `/api/chat`) and Gemini tool calling error handling.
- Files: `dashboard/api.py`, `dashboard/chat_agent.py`.
- Risk: Regressions in frontend data contracts when backend models change.
- Priority: Medium.

---

*Concerns audit: 2026-09-09*
