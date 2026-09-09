# External Integrations

**Analysis Date:** 2026-09-09

## APIs & External Services

**Network Assurance (Cisco DNA Center / Catalyst Center):**
- **Service:** Cisco DNA Center (DNAC) REST API
  - **Purpose:** Event subscription, token authentication, issue status retrieval, and network device inventory health checks.
  - **SDK/Client:** Custom HTTP client implemented in `app/dnac_client.py` and resilient monitor in `dashboard/dnac_monitor.py`.
  - **Endpoints:**
    - Authentication: `POST /dna/system/api/v1/auth/token` (HTTP Basic Auth -> JWT Bearer Token).
    - Event Subscriptions: `GET /dna/intent/api/v1/event/subscription`, `POST /dna/intent/api/v1/event/subscription` (registers webhook receiver URL).
    - Issue Enrichment: `GET /dna/intent/api/v1/issue-enrichment-details` (queries active issue status using `issueId` / `instanceId`).
    - Device Health & Active Issues: `GET /dna/intent/api/v1/issues`, `GET /dna/intent/api/v1/network-device`.
  - **Auth:** Environment variables `DNAC_USERNAME`, `DNAC_PASSWORD`, configured in `.env`.
  - **SSL Policy:** Controlled via `config.yaml` (`dnac.verify_ssl: false` by default for internal lab / appliance certificates).

**IT Service Management (ServiceNow):**
- **Service:** ServiceNow ITSM Table API
  - **Purpose:** Incident life-cycle automation for genuine or unresolving network alerts.
  - **SDK/Client:** Implemented in `workflow/tools/servicenow_client.py` and helper `consumer/helpers/snow_acknowledge.py`.
  - **Endpoints:**
    - Search Incidents: `GET {SNOW_INSTANCE_URL}/api/now/table/incident?sysparm_query=...`
    - Create Incident: `POST {SNOW_INSTANCE_URL}/api/now/table/incident`
    - Update / Reopen / Work Notes: `PUT {SNOW_INSTANCE_URL}/api/now/table/incident/{sys_id}`
  - **Auth:** Environment variables `SNOW_USERNAME`, `SNOW_PASSWORD`, `SNOW_INSTANCE_URL`.
  - **Safety Mode:** Governed by `SNOW_PUSH_ENABLED` in `.env`. When set to `no` or `false`, executes in dry-run mode without modifying live incidents.

**Generative AI & LLM (Google Gemini):**
- **Service:** Google Generative Language API (Gemini 2.0 Flash)
  - **Purpose:** Natural language network operations assistant, intelligent log querying, intent classification, and dynamic chart generation.
  - **Client:** `dashboard/chat_agent.py` implementing autonomous tool calling.
  - **Tools Exposed to LLM:**
    - `query_mongodb`: Query structured alert traces from MongoDB.
    - `query_dnac_devices`: Fetch real-time device health from DNAC.
    - `generate_visualization`: Create interactive Recharts chart configurations on the fly.
  - **Auth:** Environment variable `GEMINI_API_KEY`, base URL `GEMINI_BASE_URL` (default `https://generativelanguage.googleapis.com`).
  - **CA Handling:** `SUPPRESS_CA_BUNDLE` environment flag allows bypass of corporate proxy certificate restrictions.

**Email & Alert Notifications (SMTP):**
- **Service:** Corporate SMTP Relay
  - **Purpose:** Dispatches notification emails to operations distribution lists (DL) when alerts are suppressed as backdated, verified as auto-resolved, or escalated to ServiceNow.
  - **Client:** Implemented in `workflow/tools/email_client.py` using Python standard library `smtplib`.
  - **Config:** `config.yaml` (`email_notifications.smtp_host`, `email_notifications.smtp_port`, `email_notifications.dl_address`, `email_notifications.sender_address`).

## Data Storage

**Databases:**
- **MongoDB (NoSQL Document Store):**
  - **Connection:** `MONGO_URI` (default: `mongodb://localhost:27017`), database `MONGO_DB_NAME` (`false_alert_suppression`).
  - **Client:** `workflow/tools/mongodb_client.py` using `pymongo.MongoClient`.
  - **Collections:**
    - `alert_results`: Full evaluation state, original payload, agent execution timestamps, classifier predictions, and ServiceNow actions.
  - **Indexes:**
    - Compound unique index `dedup_composite_key`:
      - `alert_id`: 1
      - `alert_details.instance_id`: 1
      - `alert_details.device_id`: 1
      - `alert_details.raw_timestamp`: 1

**File Storage:**
- Local filesystem repository:
  - `data/simulated_alerts.json`: Fallback dataset (60+ alerts) when MongoDB is offline (`dashboard/api.py`).
  - `data/auto_resolving_alerts.json`, `data/non_auto_resolving_alerts.json`, `data/backdated_alerts.json`: Benchmark and validation datasets.
  - `status.json`: Per-run JSON artifact emitted by `workflow/nodes/node_reporter.py` for Jenkins job artifacts.
  - `models/ml_model.joblib`: Serialized TF-IDF + LogisticRegression model.
  - `models/checkpoints/checkpoint-651`: Trained DistilBERT checkpoint directory.

**Caching:**
- In-memory caching:
  - Global singleton pattern for ML and DL classifiers (`workflow/nodes/node_agent_2.py`).
  - Best-effort in-memory cache and background sync thread for device health (`dashboard/dnac_sync.py`).

## Authentication & Identity

**Auth Provider:**
- Multi-tier decentralized authentication:
  - DNAC: HTTP Basic Auth exchanged for short-lived Cisco token header `X-Auth-Token`.
  - ServiceNow: HTTP Basic Authentication headers (`Authorization: Basic <base64>`).
  - RabbitMQ: AMQP Plain Credentials (`pika.PlainCredentials(user, pass)`).
  - Jenkins: HTTP Basic Auth with API Token (`requests.auth.HTTPBasicAuth(username, token)`).
  - Gemini: API key passed as query parameter `key={GEMINI_API_KEY}`.

## Monitoring & Observability

**Error Tracking:**
- Handled via try-except wrappers and `safe_node` decorator in `workflow/utils/helpers.py`. Node errors are captured in `GraphState["results"][node]["error"]` without crashing the graph runtime.

**Logs:**
- Standard Python logging framework:
  - Webhook Ingestion Service: `app/main.py`
  - Long-running Consumers: `consumer/helpers/logger.py` writing to `logs/noops-dnac-consumer.log`
  - Workflow Execution: `workflow/utils/logger.py` redirected to `run.log` via `redirect_all_output` in `workflow/run.py`
  - Dashboard API: `logs/dashboard.log` configured in `dashboard/api.py`

## CI/CD & Deployment

**Automation Runner (Jenkins):**
- **Service:** Jenkins Master
  - **Purpose:** Isolated, containerized/agent execution of LangGraph workflows upon receiving alerts.
  - **Trigger Helper:** `consumer/helpers/jenkins_helpers.py` (`trigger_parameterized_job`).
  - **Pipelines:**
    - Main Triage: `jenkins/Jenkinsfile.main` invokes `python workflow/run.py`.
    - Delayed Recheck: `jenkins/Jenkinsfile.delayed` invokes `python workflow/run_delayed.py`.
  - **Config:** `JENKINS_URL`, `JENKINS_USERNAME`, `JENKINS_TOKEN`, `JENKINS_JOB_PATH`, `JENKINS_DELAYED_JOB_PATH`.

## Environment Configuration

**Required Environment Variables (`.env`):**
- `DNAC_USERNAME`: DNAC API user
- `DNAC_PASSWORD`: DNAC API password
- `RABBITMQ_USERNAME`: RabbitMQ broker user
- `RABBITMQ_PASSWORD`: RabbitMQ broker password
- `SNOW_INSTANCE_URL`: ServiceNow instance URL
- `SNOW_USERNAME`: ServiceNow service account
- `SNOW_PASSWORD`: ServiceNow password
- `SNOW_PUSH_ENABLED`: Toggle live ticket updates (`yes`/`no`)
- `MONGO_URI`: MongoDB connection string
- `MONGO_DB_NAME`: MongoDB database name
- `JENKINS_URL`: Jenkins base URL
- `JENKINS_USERNAME`: Jenkins user
- `JENKINS_TOKEN`: Jenkins API token
- `JENKINS_JOB_PATH`: Primary job name
- `JENKINS_DELAYED_JOB_PATH`: Delayed recheck job name
- `GEMINI_API_KEY`: Google Gemini API key

**Secrets Location:**
- Root `.env` file (must be excluded from source control via `.gitignore`).

## Webhooks & Callbacks

**Incoming:**
- `POST /api/v1/webhook` on FastAPI service (`app/main.py:103`):
  - Ingress point for Cisco DNAC alert notifications.
  - Supports single JSON objects or lists of alert events.
  - Ingestion enriches events with `_source: "dnac-webhook"` and publishes directly to RabbitMQ `dnac.alerts.q`.

**Outgoing:**
- RabbitMQ AMQP message publishing to `dnac.exchange`.
- HTTP POST to Jenkins `/job/{job_path}/buildWithParameters`.
- HTTP POST/PUT to ServiceNow `/api/now/table/incident`.
- SMTP socket push to operations distribution list.

---

*Integration audit: 2026-09-09*
