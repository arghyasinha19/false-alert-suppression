# Technology Stack

**Analysis Date:** 2026-09-09

## Languages

**Primary:**
- Python 3.13 - Backend API (`app/main.py`), Queue Consumers (`consumer/`), LangGraph Multi-Agent Workflow (`workflow/`), Machine Learning Pipelines (`workflow/classifier/`), Dashboard API (`dashboard/api.py`), and Diagnostic Scripts
- JavaScript / JSX (ECMAScript Modules) - Interactive React 19 Frontend Dashboard (`dashboard/src/`)

**Secondary:**
- HTML5 / CSS3 - Presentation (`presentation.html`), One-Pagers (`executive_one_pager.html`, `business_head_one_pager.html`), Documentation (`documentation/*.html`), and Custom Glassmorphic CSS styling (`dashboard/src/*.css`)
- Groovy / Jenkins Pipeline DSL - CI/CD pipeline automation (`jenkins/Jenkinsfile.main`, `jenkins/Jenkinsfile.delayed`)
- YAML - Application configuration (`config.yaml`) and GitHub/agent configuration

## Runtime

**Environment:**
- Python 3.13 runtime environment (configured via `requirements.txt` compiled from `requirements.in`)
- Node.js (v18+) runtime environment for React Vite SPA development and bundling (`dashboard/package.json`)

**Package Manager:**
- Python: `pip` / `pip-tools` (`pip-compile requirements.in` -> `requirements.txt`)
  - Lockfile: `requirements.txt` present (pinned versions)
- Node.js: `npm` (`dashboard/package.json`)
  - Lockfile: `dashboard/package-lock.json` present

## Frameworks

**Core:**
- FastAPI 0.117.1 - REST API for Cisco DNAC webhook ingestion (`app/main.py`) and Traceability Dashboard backend (`dashboard/api.py`)
- LangGraph (`langgraph`, `langchain-core`) - StateGraph multi-agent decision engine (`workflow/graph.py`, `workflow/state.py`)
- React 19.2.7 - Frontend user interface with glassmorphic design (`dashboard/src/App.jsx`)
- Vite 8.1.0 - Fast build tool and development server for dashboard (`dashboard/vite.config.js`)

**Data Science & Machine Learning:**
- Scikit-learn 1.7.x - TF-IDF vectorization and Logistic Regression classifier (`workflow/classifier/model_ml.py`)
- PyTorch 2.x & Hugging Face Transformers - Fine-tuned DistilBERT deep learning classification (`workflow/classifier/model.py`)
- ONNX Runtime 1.22.0 - High-performance CPU inference for DistilBERT (`workflow/classifier/model.py`)
- Sentence-Transformers 3.x (`all-MiniLM-L6-v2`) - Semantic vector embeddings for alert log pattern clustering (`dashboard/alert_clustering.py`)
- HDBSCAN 0.8.x - Density-based unsupervised clustering of alert templates (`dashboard/alert_clustering.py`)
- Pandas & NumPy - Data structures, matrix operations, and metric calculations

**Messaging & Persistence:**
- Pika 1.3.2 - AMQP 0-9-1 client library for RabbitMQ connection and message lifecycle (`app/mq_publisher.py`, `consumer/noops_dnac_consumer.py`)
- PyMongo 4.x - Official MongoDB driver for storing alert execution state and composite deduplication (`workflow/tools/mongodb_client.py`)

**Visualization & UI Components:**
- Recharts 3.9.0 - SVG-based charting library for dashboard KPIs and trends (`dashboard/src/FalseAlertMetrics.jsx`, `dashboard/src/ChatChart.jsx`)
- Lucide React 1.22.0 - Modern icon system (`dashboard/src/App.jsx`, `dashboard/src/NetworkOperations.jsx`)

**Build/Dev:**
- Uvicorn 0.35.0 - Asynchronous ASGI web server for FastAPI services
- Oxlint 1.69.0 - High-performance Rust-based JavaScript/JSX linter (`dashboard/.oxlintrc.json`)
- Dotenv (`python-dotenv`) - Environment variable loader (`.env`)

## Key Dependencies

**Critical:**
- `langgraph`: Core decision engine building state transitions across Agent 1 (Backdate), Agent 2 (Classifier), Agent 3 (Scheduler), Agent 4 (ServiceNow), Notifier, and Reporter (`workflow/graph.py`).
- `pika`: Manages reliable queue publishing, message acknowledgments, DLX wait queue delays, and connection recovery (`app/mq_publisher.py`, `consumer/`).
- `onnxruntime`: Provides fast CPU inference for DistilBERT without requiring heavy GPU infrastructure in production (`workflow/classifier/model.py`).
- `scikit-learn` & `joblib`: Fast-path lightweight classifier (`models/ml_model.joblib`) deployed to classify alerts with minimal latency.
- `pymongo`: Persists end-to-end alert evaluation traces, providing the single source of truth for the dashboard (`workflow/tools/mongodb_client.py`).
- `requests`: Powers HTTP REST communication with Cisco DNA Center (`app/dnac_client.py`), ServiceNow (`workflow/tools/servicenow_client.py`), Jenkins API (`consumer/helpers/jenkins_helpers.py`), and Google Gemini API (`dashboard/chat_agent.py`).

**Infrastructure:**
- `pydantic 2.x`: Request validation and data models for FastAPI endpoints.
- `pyyaml`: Parses central application settings from `config.yaml`.
- `urllib3`: Low-level HTTP transport with SSL control.

## Configuration

**Environment:**
- Managed through `.env` in the project root.
- Required credentials and endpoints:
  - `DNAC_USERNAME`, `DNAC_PASSWORD`: Cisco DNA Center authentication.
  - `RABBITMQ_USERNAME`, `RABBITMQ_PASSWORD`, `RABBITMQ_HOST`: Message broker connection.
  - `SNOW_INSTANCE_URL`, `SNOW_USERNAME`, `SNOW_PASSWORD`, `SNOW_PUSH_ENABLED`: ServiceNow Table API access and dry-run flag.
  - `MONGO_URI`, `MONGO_DB_NAME`: MongoDB persistence connection string and database name.
  - `JENKINS_URL`, `JENKINS_USERNAME`, `JENKINS_TOKEN`, `JENKINS_JOB_PATH`, `JENKINS_DELAYED_JOB_PATH`: CI/CD automation runner credentials.
  - `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_BASE_URL`: Google Gemini generative AI agent configuration.

**Application Configuration:**
- Central YAML file: `config.yaml`
  - DNAC base URL, webhook receiver settings, and SSL verification options.
  - RabbitMQ exchange, main queue, and delayed wait queue configuration.
  - Ingestion server host and port.
  - Classifier model checkpoint paths and confidence thresholds.
  - Email notification toggles (backdated, auto-resolved, ServiceNow push).

**Build:**
- Frontend: `dashboard/vite.config.js` with `@vitejs/plugin-react`.
- Python dependencies: `requirements.in` and `requirements.txt`.

## Platform Requirements

**Development:**
- Windows / Linux / macOS with Python 3.13+ and Node.js 18+.
- Local or containerized MongoDB instance (`mongodb://localhost:27017`).
- Local or containerized RabbitMQ instance with DLX exchange configuration.

**Production:**
- Host or Kubernetes/Docker container deployment.
- Cisco DNA Center (DNAC) version 2.2+ with webhook notification egress.
- ServiceNow instance with ITSM Incident Table API permissions.
- Jenkins master/agent infrastructure for parameterized workflow execution.

---

*Stack analysis: 2026-09-09*
