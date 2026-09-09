# Codebase Structure

**Analysis Date:** 2026-09-09

## Directory Layout

```
false-alert-suppression/
├── app/                        # Webhook receiver FastAPI service & DNAC client
│   ├── dnac_client.py          # Cisco DNAC REST client & subscription management
│   ├── main.py                 # FastAPI webhook listener & route endpoints
│   └── mq_publisher.py         # RabbitMQ publisher for ingested alerts
├── consumer/                   # Long-running background queue consumers
│   ├── config/
│   │   └── rabbitmq.py         # Consumer RabbitMQ queue/vhost configurations
│   ├── consumer-delay-queue.py # Consumer for 15m delayed wait queue
│   ├── helpers/                # Consumer utilities (Jenkins, logging, RabbitMQ, SNOW)
│   │   ├── generic_helpers.py  # JSON parsing & field extraction
│   │   ├── jenkins_helpers.py  # Jenkins REST client triggering parameterized builds
│   │   ├── logger.py           # File & stream logging setup
│   │   ├── rabbitmq_helpers.py # AMQP channel and publish helpers
│   │   ├── snow_acknowledge.py # ServiceNow acknowledgment helpers
│   │   └── trace_store.py      # Trace store utility
│   └── noops_dnac_consumer.py  # Main RabbitMQ consumer daemon
├── dashboard/                  # Operations Dashboard (FastAPI + Vite React SPA)
│   ├── alert_clustering.py     # HDBSCAN + Sentence-Transformers pattern clusterer
│   ├── api.py                  # Dashboard FastAPI backend (port 8004)
│   ├── chat_agent.py           # Gemini 2.0 Flash tool-calling chat assistant
│   ├── dnac_monitor.py         # Non-raising resilient DNAC health checker
│   ├── dnac_sync.py            # Periodic background device synchronizer
│   ├── package.json            # Node.js dependencies (React 19, Vite 8, Recharts 3)
│   ├── src/                    # React frontend application
│   │   ├── AlertPatterns.jsx   # Pattern clustering view
│   │   ├── App.css / App.jsx   # Shell layout, navigation, and sidebar
│   │   ├── ChatChart.jsx       # Dynamic chart renderer for AI assistant responses
│   │   ├── ChatPanel.jsx       # Interactive slide-over Ops Assistant chat UI
│   │   ├── FalseAlertMetrics.jsx # Suppression KPIs, donut charts, and alert tables
│   │   ├── NetworkOperations.jsx # Device health grid & active issue badges
│   │   └── main.jsx            # React root mount
│   └── vite.config.js          # Vite build & development configuration
├── data/                       # Test datasets and fallback alert payloads
│   ├── auto_resolving_alerts.json
│   ├── backdated_alerts.json
│   ├── non_auto_resolving_alerts.json
│   └── simulated_alerts.json
├── documentation/              # Architecture documents, user manuals, HTML guides
│   ├── architecture_design_document.md
│   ├── deployment_guide.html
│   ├── mongodb_setup.md
│   ├── rabbitmq_dlx_setup.md
│   └── walkthrough.md
├── jenkins/                    # Jenkins CI/CD pipeline definitions
│   ├── Jenkinsfile.main        # Main triage execution pipeline
│   └── Jenkinsfile.delayed     # Delayed re-check execution pipeline
├── models/                     # Trained ML model weights and serializations
│   └── ml_model.joblib         # Serialized TF-IDF + Logistic Regression model
├── workflow/                   # Core LangGraph decision engine
│   ├── classifier/             # Model architectures and training scripts
│   │   ├── model.py            # DistilBERT classifier (PyTorch & ONNX Runtime)
│   │   ├── model_ml.py         # TF-IDF + Logistic Regression classifier
│   │   ├── preprocessor.py     # Text cleaning & regex normalization
│   │   ├── train_ml.py         # ML model training script
│   │   └── train_model.py      # DistilBERT fine-tuning script
│   ├── graph.py                # LangGraph StateGraph topology definition
│   ├── nodes/                  # Individual LangGraph node implementations
│   │   ├── node_agent_1.py     # Agent 1: Backdate detector node
│   │   ├── node_agent_2.py     # Agent 2: ML/DL classifier node
│   │   ├── node_agent_3_scheduler.py # Agent 3: RabbitMQ delay queue scheduler node
│   │   ├── node_agent_4_servicenow.py # Agent 4: ServiceNow incident management node
│   │   ├── node_email_notifier.py # Notification node
│   │   ├── node_reporter.py    # Final reporting & MongoDB upsert node
│   │   └── node_supervisor.py  # Conditional routing node
│   ├── run.py                  # Entry point for Jenkins main triage
│   ├── run_delayed.py          # Entry point for Jenkins delayed re-check
│   ├── state.py                # GraphState TypedDict definition
│   ├── tools/                  # Reusable integrations and clients
│   │   ├── backdate_detector.py # Timestamp skew evaluator
│   │   ├── email_client.py     # SMTP email client
│   │   ├── message_broker.py   # RabbitMQ broker client for delayed queue
│   │   ├── mongodb_client.py   # MongoDB persistence client with dedup index
│   │   └── servicenow_client.py # ServiceNow Table API REST client
│   └── utils/
│       ├── helpers.py          # Safe node decorator and runtime helpers
│       └── logger.py           # Standardized logger configuration
├── config.yaml                 # Central configuration for DNAC, RabbitMQ, and classifier
├── requirements.in             # Top-level direct Python dependencies
├── requirements.txt            # Pinned lockfile generated via pip-compile
└── status.json                 # Output summary artifact generated by workflow runs
```

## Directory Purposes

**`app/`:**
- Purpose: Network edge webhook receiver service.
- Contains: FastAPI web service, DNAC API client, RabbitMQ publisher.
- Key files: `app/main.py`, `app/dnac_client.py`, `app/mq_publisher.py`.

**`consumer/`:**
- Purpose: Long-running AMQP queue listeners.
- Contains: Background daemon processes and Jenkins trigger wrappers.
- Key files: `consumer/noops_dnac_consumer.py`, `consumer/consumer-delay-queue.py`, `consumer/helpers/jenkins_helpers.py`.

**`workflow/`:**
- Purpose: LangGraph multi-agent decision engine.
- Contains: Node implementations, routing logic, model inferencing, integration tools, and CLI runners.
- Key files: `workflow/graph.py`, `workflow/state.py`, `workflow/run.py`, `workflow/run_delayed.py`.

**`dashboard/`:**
- Purpose: Operations visibility, metrics monitoring, pattern clustering, and conversational AI.
- Contains: FastAPI backend (`dashboard/api.py`), React 19 SPA (`dashboard/src/`), and Gemini LLM agent (`dashboard/chat_agent.py`).
- Key files: `dashboard/api.py`, `dashboard/chat_agent.py`, `dashboard/src/App.jsx`.

**`jenkins/`:**
- Purpose: Continuous execution infrastructure.
- Contains: Declarative Groovy Jenkinsfiles for containerized execution.
- Key files: `jenkins/Jenkinsfile.main`, `jenkins/Jenkinsfile.delayed`.

**`data/`:**
- Purpose: Test payloads, synthetic alerts, and offline fallbacks.
- Contains: JSON datasets representing auto-resolving, backdated, and non-auto-resolving network alerts.
- Key files: `data/simulated_alerts.json`, `data/auto_resolving_alerts.json`.

## Key File Locations

**Entry Points:**
- Webhook Ingestion API: `app/main.py`
- Main Queue Consumer: `consumer/noops_dnac_consumer.py`
- Delayed Queue Consumer: `consumer/consumer-delay-queue.py`
- Main Triage Execution: `workflow/run.py`
- Delayed Triage Execution: `workflow/run_delayed.py`
- Dashboard API: `dashboard/api.py`
- Dashboard Frontend: `dashboard/src/main.jsx`

**Configuration:**
- Main Config: `config.yaml`
- Secret Environment Variables: `.env`
- Consumer RabbitMQ Settings: `consumer/config/rabbitmq.py`
- Frontend Build Config: `dashboard/vite.config.js`
- Linter Config: `dashboard/.oxlintrc.json`

**Core Logic:**
- Graph Definition: `workflow/graph.py`
- State Schema: `workflow/state.py`
- Backdate Evaluation: `workflow/tools/backdate_detector.py`
- Text Classification: `workflow/classifier/model_ml.py`, `workflow/classifier/model.py`
- Delayed Scheduler: `workflow/nodes/node_agent_3_scheduler.py`
- ServiceNow Management: `workflow/tools/servicenow_client.py`
- MongoDB Client: `workflow/tools/mongodb_client.py`
- Pattern Clustering: `dashboard/alert_clustering.py`

**Testing & Diagnostics:**
- Unit Fallback Tests: `test_dnac_fallback.py`
- Ensemble Classifier Test: `test_ensemble.py`
- Payload Extraction Test: `test_payload_extraction.py`
- RabbitMQ Config Check: `test_rmq.py`
- API Verification: `check_api.py`
- MongoDB Check: `check_mongo.py`

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `dnac_client.py`, `backdate_detector.py`)
- LangGraph nodes: `node_<agent_name>.py` (e.g., `node_agent_1.py`, `node_supervisor.py`)
- React components: `PascalCase.jsx` (e.g., `FalseAlertMetrics.jsx`, `ChatPanel.jsx`)
- Style sheets: Matching component name or purpose (e.g., `App.css`, `ChatPanel.css`, `index.css`)
- Documentation: `snake_case.md` or `UPPERCASE.md` (e.g., `architecture_design_document.md`, `README.md`)

**Directories:**
- Top-level and subpackages: `snake_case` or single lowercase word (e.g., `app`, `consumer`, `workflow/classifier`, `workflow/nodes`, `workflow/tools`)

## Where to Add New Code

**New Agent or Evaluation Node:**
- 1. Implement agent logic in `workflow/nodes/node_<new_agent>.py`.
- 2. Define any supporting tools in `workflow/tools/<new_tool>.py`.
- 3. Add any required state keys in `workflow/state.py` (`AgentResult` or `GraphState`).
- 4. Register node and wire transitions in `workflow/graph.py` using `safe_node("<name>", ...)`.
- 5. Update `workflow/nodes/node_reporter.py` if custom metrics need persistence to MongoDB.

**New External Integration (e.g., PagerDuty, Slack, Jira):**
- 1. Create client class under `workflow/tools/<service>_client.py`.
- 2. Add credentials and toggle switches to `config.yaml` and `.env`.
- 3. Call client within a specialized node or attach to `workflow/nodes/node_email_notifier.py`.

**New Dashboard View or Visualization:**
- 1. Add API endpoint in `dashboard/api.py`.
- 2. Create React view component under `dashboard/src/<ViewName>.jsx`.
- 3. Add navigation item and view state routing in `dashboard/src/App.jsx`.
- 4. Add tool definition to `dashboard/chat_agent.py` if the AI assistant should be able to query it.

## Special Directories

- `models/`: Holds serialized ML binary models (`ml_model.joblib`) and deep learning checkpoints (`checkpoint-651`). Large checkpoints should be tracked with Git LFS or mounted via object store.
- `logs/`: Runtime log files generated by background consumers and dashboard APIs (`logs/dashboard.log`, `logs/noops-dnac-consumer.log`). Not committed to version control.
- `data/`: Contains static and synthetic JSON datasets used for local offline simulation and unit testing.
- `.planning/`: GSD project planning artifacts, state, and codebase maps.

---

*Structure analysis: 2026-09-09*
