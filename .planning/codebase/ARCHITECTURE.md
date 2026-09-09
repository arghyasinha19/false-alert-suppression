<!-- refreshed: 2026-09-09 -->
# Architecture

**Analysis Date:** 2026-09-09

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          1. INGESTION & EVENT INGRESS                       │
├──────────────────────────────────────┬──────────────────────────────────────┤
│  Cisco DNA Center (Webhook Push)     │  FastAPI Webhook Receiver Service    │
│  `[External Cisco Appliance]`        │  `app/main.py`                       │
└──────────────────┬───────────────────┴──────────────────┬───────────────────┘
                   │                                      │
                   ▼ (AMQP Publish)                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          2. BUFFERING & RETRY QUEUE                         │
│  RabbitMQ Exchange (`dnac.exchange`) & Main Queue (`dnac.alerts.q`)        │
│  `app/mq_publisher.py` | `consumer/noops_dnac_consumer.py`                 │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Trigger Parameterized Build)
┌─────────────────────────────────────────────────────────────────────────────┐
│                          3. CI/CD ORCHESTRATION LAYER                       │
│  Jenkins Automation Pipeline: `jenkins/Jenkinsfile.main`                     │
│  `consumer/helpers/jenkins_helpers.py`                                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Executes `python workflow/run.py`)
┌─────────────────────────────────────────────────────────────────────────────┐
│                  4. DECISION BRAIN: LangGraph State Machine                 │
│                                                                             │
│  ┌───────────────────────┐                                                  │
│  │ Agent 1: Backdate     │  Evaluates skew vs 24h threshold                 │
│  │ `nodes/node_agent_1`  │  `tools/backdate_detector.py`                    │
│  └───────────┬───────────┘                                                  │
│              ▼                                                              │
│  ┌───────────────────────┐                                                  │
│  │ Supervisor Router     │  Backdated? ──Yes──► [Email Notifier]            │
│  │ `node_supervisor.py`  │          │                                       │
│  └───────────┬───────────┘          └──No                                   │
│              ▼                                                              │
│  ┌───────────────────────┐                                                  │
│  │ Agent 2: Classifier   │  TF-IDF/LogReg -> Fallback DistilBERT            │
│  │ `nodes/node_agent_2`  │  `classifier/model_ml.py`, `classifier/model.py` │
│  └───────────┬───────────┘                                                  │
│              ▼                                                              │
│  ┌───────────────────────┐                                                  │
│  │ Agent 3: Scheduler    │  Auto-Resolving? ──Yes──► Wait Queue (15m TTL)   │
│  │ `node_agent_3`        │                                                  │
│  └───────────┬───────────┘                                                  │
│              ▼                                                              │
│  ┌───────────────────────┐                                                  │
│  │ Agent 4: ServiceNow   │  Non-Auto Resolving? ──► Active / Reopen / Create│
│  │ `node_agent_4`        │  `tools/servicenow_client.py`                    │
│  └───────────┬───────────┘                                                  │
│              ▼                                                              │
│  ┌───────────────────────┐                                                  │
│  │ Email Notifier        │  Dispatches operational alert emails             │
│  │ `node_email_notifier` │  `tools/email_client.py`                         │
│  └───────────┬───────────┘                                                  │
│              ▼                                                              │
│  ┌───────────────────────┐                                                  │
│  │ Reporter Node         │  Emits status.json & upserts MongoDB trace       │
│  │ `node_reporter.py`    │  `tools/mongodb_client.py`                       │
│  └───────────────────────┘                                                  │
└──────────────────┬──────────────────────────────────────┬───────────────────┘
                   │                                      │
                   ▼ (15m Delay Loop)                     ▼ (Persist Trace)
┌──────────────────────────────────────┐  ┌───────────────────────────────────┐
│ 5. DELAYED VERIFICATION LOOP         │  │ 6. PERSISTENCE & VISUALIZATION    │
│ RabbitMQ DLX -> Wait Queue           │  │ MongoDB: `alert_results` coll     │
│ `consumer/consumer-delay-queue.py`   │  │ FastAPI: `dashboard/api.py`       │
│ Jenkins: `Jenkinsfile.delayed`       │  │ React SPA: `dashboard/src/`       │
│ Script: `workflow/run_delayed.py`    │  │ Gemini Agent: `chat_agent.py`     │
└──────────────────────────────────────┘  └───────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **Webhook Receiver** | Authenticates with DNAC, accepts push webhook alerts, enriches payloads, and publishes to RabbitMQ | `app/main.py`, `app/mq_publisher.py` |
| **DNAC API Client** | Manages DNAC token authentication, webhook registrations, and device/issue lookups | `app/dnac_client.py` |
| **Main Queue Consumer** | Long-running AMQP worker consuming from `dnac.alerts.q`, normalizes payloads, and triggers Jenkins triage pipeline | `consumer/noops_dnac_consumer.py` |
| **Delayed Queue Consumer** | Listens for expired messages evicted from 15-minute wait queue, triggers delayed Jenkins pipeline | `consumer/consumer-delay-queue.py` |
| **Main Triage Runner** | Entry point for Jenkins job, handles headless logging redirection, invokes LangGraph, writes `status.json` | `workflow/run.py` |
| **Delayed Triage Runner** | Re-queries DNAC to verify if alert resolved after 15m delay; escalates to ServiceNow if still active | `workflow/run_delayed.py` |
| **LangGraph Topology** | Builds directed state graph compiling nodes, edges, conditional supervisor routing, and error boundaries | `workflow/graph.py`, `workflow/state.py` |
| **Agent 1 (Backdate)** | Inspects event timestamps against 24-hour skew threshold to filter stale, historical, or invalid alerts | `workflow/nodes/node_agent_1.py`, `workflow/tools/backdate_detector.py` |
| **Supervisor Router** | Directs graph traffic: routes backdated alerts directly to email/reporter; passes current alerts to Agent 2 | `workflow/nodes/node_supervisor.py` |
| **Agent 2 (Classifier)** | Hierarchical NLP classifier: evaluates alert text with TF-IDF/LogisticRegression; falls back to DistilBERT | `workflow/nodes/node_agent_2.py`, `workflow/classifier/model_ml.py`, `workflow/classifier/model.py` |
| **Agent 3 (Scheduler)** | Intercepts `Auto resolving` alerts and schedules a 15-minute delay via RabbitMQ Dead Letter Exchange | `workflow/nodes/node_agent_3_scheduler.py`, `workflow/tools/message_broker.py` |
| **Agent 4 (ServiceNow)** | Queries ServiceNow for active/recent incidents on device; appends comments, reopens, or creates new incidents | `workflow/nodes/node_agent_4_servicenow.py`, `workflow/tools/servicenow_client.py` |
| **Email Notifier** | Dispatches email alerts to DL on suppression or ticket creation | `workflow/nodes/node_email_notifier.py`, `workflow/tools/email_client.py` |
| **Reporter** | Calculates overall execution status (`success`, `partial_failure`, `failed`), writes `status.json`, upserts MongoDB | `workflow/nodes/node_reporter.py`, `workflow/tools/mongodb_client.py` |
| **Dashboard API** | Exposes REST endpoints (`/api/alerts`, `/api/devices`, `/api/chat`) with MongoDB queries and DNAC monitoring | `dashboard/api.py` |
| **Gemini Chat Agent** | Autonomous multi-step tool-calling agent answering natural language operational inquiries and generating charts | `dashboard/chat_agent.py` |
| **Alert Clustering Engine** | Regex variable tokenization, sentence-embedding extraction, and HDBSCAN clustering of recurrent alerts | `dashboard/alert_clustering.py` |
| **React Dashboard SPA** | Glassmorphic operator interface displaying metrics, NOC health grid, pattern clusters, and conversational AI | `dashboard/src/App.jsx` |

## Pattern Overview

**Overall Architecture:** Event-Driven Asynchronous Pipeline with LangGraph Multi-Agent State Machine and Decoupled Microservices.

**Key Characteristics:**
- **Decoupled Buffer-First Ingress:** Webhook endpoints do not execute heavy ML inference inline; they quickly acknowledge HTTP requests and offload to RabbitMQ.
- **Fail-Soft Isolation (Safe Nodes):** Every agent node in LangGraph is wrapped in `safe_node()` decorator (`workflow/utils/helpers.py`), preventing unhandled runtime exceptions in one node from crashing the pipeline.
- **Hierarchical Classification:** Ensemble of lightweight Scikit-Learn TF-IDF model for instant inference (~1ms) with transparent fallback to DistilBERT ONNX model for low-confidence classifications.
- **Hardware-Independent Delay:** Uses RabbitMQ message TTL and Dead-Letter Exchanges instead of sleeping processes or cron pollers.
- **Resilient Traceability:** The frontend queries MongoDB, but seamlessly degrades to local simulated data (`data/simulated_alerts.json`) if the database is offline.

## Layers

**Ingress Layer:**
- Purpose: Accept push alerts from network controllers.
- Location: `app/main.py`, `app/dnac_client.py`, `app/mq_publisher.py`
- Depends on: FastAPI, Pika, Cisco DNAC REST API
- Used by: Cisco DNA Center Webhook Subscriptions

**Message Queuing Layer:**
- Purpose: Asynchronous buffering, retry management, and delayed scheduling.
- Location: `consumer/`, `workflow/tools/message_broker.py`
- Depends on: RabbitMQ broker, Pika
- Used by: Webhook receiver and Jenkins job triggers

**Orchestration & Workflow Layer:**
- Purpose: Execute stateful multi-agent triage logic.
- Location: `workflow/`
- Depends on: LangGraph, Scikit-learn, ONNX Runtime, Transformers, PyTorch, PyMongo
- Used by: Jenkins build runners (`Jenkinsfile.main`, `Jenkinsfile.delayed`)

**Integration & Egress Layer:**
- Purpose: Interact with external systems of record.
- Location: `workflow/tools/servicenow_client.py`, `workflow/tools/email_client.py`
- Depends on: ServiceNow REST API, SMTP Relay

**Presentation & Analytics Layer:**
- Purpose: Operational observability, pattern clustering, and operator interaction.
- Location: `dashboard/`
- Depends on: React 19, Vite, Recharts, FastAPI, Google Gemini API, HDBSCAN, Sentence-Transformers

## Data Flow

### Primary Request Path (Immediate Triage)

1. Cisco DNAC triggers webhook `POST /api/v1/webhook` (`app/main.py:103`).
2. FastAPI validates JSON, attaches `_source: "dnac-webhook"`, and publishes to `dnac.alerts.q` (`app/main.py:127`).
3. `consumer/noops_dnac_consumer.py` consumes message, sanitizes/flattens keys, and calls `JenkinsHelper.trigger_parameterized_job` (`consumer/noops_dnac_consumer.py:215`).
4. Jenkins launches `python workflow/run.py --event_id ...` (`jenkins/Jenkinsfile.main`).
5. `workflow/run.py` compiles `build_graph()` and invokes `initial_state` (`workflow/run.py:172`).
6. `agent_1` evaluates timestamp via `BackdateDetector` (`workflow/nodes/node_agent_1.py:27`).
7. `supervisor` evaluates `agent_1`:
   - If backdated: routes to `email_notifier` -> `reporter` -> END (`workflow/nodes/node_supervisor.py:55`).
   - If fresh: routes to `agent_2` (`workflow/nodes/node_supervisor.py:82`).
8. `agent_2` classifies description via ML classifier (with DL fallback) (`workflow/nodes/node_agent_2.py:115`).
9. `agent_3` intercepts alert:
   - If `Auto resolving`: publishes payload to `dnac.alerts.wait.q` with 15m TTL (`workflow/nodes/node_agent_3_scheduler.py:44`).
   - If `Non-Auto Resolving`: passes through to `agent_4`.
10. `agent_4` checks ServiceNow for device incidents and appends comment, reopens, or creates new incident (`workflow/nodes/node_agent_4_servicenow.py:52`).
11. `email_notifier` sends notification email if configured criteria met (`workflow/nodes/node_email_notifier.py:40`).
12. `reporter` records output, writes `status.json`, and updates MongoDB `alert_results` (`workflow/nodes/node_reporter.py:25`).

### Delayed Verification Flow (Self-Healing Verification)

1. Message sits in `dnac.alerts.wait.q` for 15 minutes (900,000 ms).
2. RabbitMQ expires TTL and moves message to Dead-Letter Exchange `dnac.exchange` -> `dnac.alerts.delayed`.
3. `consumer/consumer-delay-queue.py` consumes message and triggers Jenkins delayed pipeline (`consumer/consumer-delay-queue.py:64`).
4. Jenkins executes `python workflow/run_delayed.py` (`jenkins/Jenkinsfile.delayed`).
5. `check_dnac_status()` queries Cisco DNAC API to verify whether alert is still `ACTIVE` or `RESOLVED` (`workflow/run_delayed.py:93`).
6. If resolved: flags alert as suppressed, notifies email, and writes final status.
7. If still active: invokes `agent_4_servicenow` to escalate to ServiceNow (`workflow/run_delayed.py:230`).

## Key Abstractions

- `GraphState` (`workflow/state.py`): TypedDict maintaining global workflow context, alert dictionary, node results dictionary, remarks, and `next_node` route.
- `BackdateDetector` (`workflow/tools/backdate_detector.py`): Time-skew evaluator producing frozen `BackdateDecision` objects.
- `MLAlertClassifier` (`workflow/classifier/model_ml.py`): Scikit-learn TF-IDF + Logistic Regression pipeline wrapper.
- `AlertClassifier` (`workflow/classifier/model.py`): PyTorch / ONNX Runtime dual-backend DistilBERT inference wrapper.
- `RabbitMQBroker` (`workflow/tools/message_broker.py`): AMQP interface for delay queues, message publishing, and DLX routing.
- `MongoDBClient` (`workflow/tools/mongodb_client.py`): Database interface implementing composite deduplication upserts.
- `ServiceNowClient` (`workflow/tools/servicenow_client.py`): Table API client executing query building, comment updates, reopening, and incident creation.

## Entry Points

- **Webhook Ingress:** `app/main.py` (`uvicorn app.main:app --host 0.0.0.0 --port 8000`)
- **Queue Consumer (Main):** `consumer/noops_dnac_consumer.py` (`python consumer/noops_dnac_consumer.py`)
- **Queue Consumer (Delayed):** `consumer/consumer-delay-queue.py` (`python consumer/consumer-delay-queue.py`)
- **Triage Pipeline Runner:** `workflow/run.py` (`python workflow/run.py --event_id ...`)
- **Delayed Pipeline Runner:** `workflow/run_delayed.py` (`python workflow/run_delayed.py --event_id ...`)
- **Dashboard Backend:** `dashboard/api.py` (`uvicorn dashboard.api:app --port 8004`)
- **Dashboard Frontend:** `dashboard/src/main.jsx` (`npm run dev` in `dashboard/`)

## Architectural Constraints

- **Single-Threaded AMQP Event Loop:** The Pika blocking connection in consumers runs in a single thread per process; worker crashes require process supervisor (e.g. systemd/supervisord).
- **Global Classifier Singletons:** `workflow/nodes/node_agent_2.py` caches ML and DL models at module level (`_ml_classifier`, `_dl_classifier`) to avoid reloading weights (~250MB) on every graph invocation.
- **Stateless Agent Execution:** Graph nodes must remain pure functions transforming `GraphState` without saving local node state between invocations.
- **Fail-Safe Secret Loading:** The codebase uses `find_dotenv()` to walk up the directory tree to guarantee `.env` discovery across any launch directory.

## Anti-Patterns

### Anti-Pattern 1: Unhandled Node Crash Terminating Graph
**What happens:** If a downstream service (ServiceNow or RabbitMQ) throws an unexpected connection error, the entire LangGraph process crashes ungracefully.
**Why it's wrong:** Jenkins pipeline fails with exit code 1 without writing a structured `status.json` or updating MongoDB.
**Do this instead:** Wrap all node functions in `safe_node` (`workflow/utils/helpers.py`), returning `{ "ok": False, "error": str(e) }` and allowing `reporter` to calculate partial failure.

### Anti-Pattern 2: Blocking Sleeps for Delayed Evaluation
**What happens:** Using `time.sleep(900)` in worker processes to wait for alert resolution.
**Why it's wrong:** Consumes process memory, ties up execution slots in Jenkins, and risks loss of alert state on worker restart.
**Do this instead:** Use RabbitMQ Dead-Letter Exchange with message TTL (`dnac.alerts.wait.q`), letting the broker manage delays statelessly (`workflow/tools/message_broker.py`).

## Error Handling

**Strategy:** Fail-Soft Resilient Degradation.

**Patterns:**
- `safe_node` decorator catches exceptions in every graph node and stores error strings in `state["results"][node]["error"]`.
- The dashboard API catches MongoDB connection failures and immediately falls back to `data/simulated_alerts.json` (`dashboard/api.py:83`).
- ServiceNow API failures in `node_agent_4_servicenow.py` return `ok: False` with descriptive remarks, allowing the pipeline to complete and record the incident failure.

## Cross-Cutting Concerns

- **Logging:** Centralized log formatting (`%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`). Headless runners (`run.py`, `run_delayed.py`) redirect internal noise to `run.log` via `redirect_all_output()` to keep Jenkins console clean.
- **Validation:** Pydantic models for incoming JSON webhooks and `normalize_json_payload()` in consumers to handle nested Cisco DNAC variations.
- **Authentication:** Token caching and automated re-authentication in `app/dnac_client.py`.

---

*Architecture analysis: 2026-09-09*
