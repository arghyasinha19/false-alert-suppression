# False Alert Suppression - Codebase Walkthrough

This document provides a comprehensive overview of the `false-alert-suppression` codebase. It outlines the architecture, data flow, component details, and observations about the current state of the project.

## Architecture Overview

The system is designed to ingest alerts from Cisco DNA Center (DNAC), buffer them using RabbitMQ, and process them through a Jenkins-orchestrated machine-learning pipeline (LangGraph) to suppress "false" or non-actionable alerts.

The architecture consists of three main components:

1. **Webhook Receiver (`app/`)**: A FastAPI service that receives push notifications from DNAC and publishes them to a message queue.
2. **Message Queue Consumer (`consumer/`)**: A RabbitMQ consumer that listens for new alerts and triggers a Jenkins pipeline for processing.
3. **Workflow Pipeline (`workflow/`)**: A LangGraph-based triage pipeline (likely executed by Jenkins) that determines if the alert should be suppressed using business logic and a DistilBERT machine learning model.

## Component Breakdown

### 1. Webhook Receiver (`app/`)
- **[app/main.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/app/main.py)**: The FastAPI entry point. It exposes a `/api/v1/webhook` endpoint which accepts JSON payloads from DNAC. The events are enriched with metadata (`_source: dnac-webhook`) and published to RabbitMQ.
- **[app/dnac_client.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/app/dnac_client.py)**: A client for authenticating and managing webhook subscriptions on the DNAC side.
- **[app/mq_publisher.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/app/mq_publisher.py)**: A helper to publish messages reliably to RabbitMQ.

### 2. RabbitMQ Consumer (`consumer/`)
- **[consumer/noops_dnac_consumer.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/consumer/noops_dnac_consumer.py)**: A Python script acting as a long-running RabbitMQ consumer. It listens to the `dnac.alerts.q` queue.
- **Behavior**: Upon receiving an alert, it flattens/normalizes the JSON payload and triggers a parameterized Jenkins job (using `JenkinsHelper`). The Jenkins job is expected to execute the ML pipeline. If the processing fails repeatedly, the message is sent to a Dead Letter Queue (DLQ).

### 3. Workflow Pipeline (`workflow/`)
This is the core decision-engine, leveraging LangGraph to construct a multi-agent state graph.

- **[workflow/run.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/run.py)**: The entry point designed to run inside Jenkins. It suppresses noisy logs, parses Jenkins parameters, initializes the LangGraph state, and executes `graph.invoke(initial_state)`. It produces a `status.json` file as an artifact.
- **[workflow/graph/graph.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/graph/graph.py)**: Defines the LangGraph workflow topology: `agent_1` → `supervisor` → conditionally routes to `agent_2` or `reporter`.
- **Agents & Nodes**:
  - **[workflow/nodes/node_agent_1.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/nodes/node_agent_1.py)**: Runs the `BackdateDetector` ([workflow/agents/backdate_detector.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/agents/backdate_detector.py)) to identify if the alert is "backdated" (e.g., delayed beyond a threshold, or incorrectly dated).
  - **[workflow/nodes/node_supervisor.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/nodes/node_supervisor.py)**: Analyzes `agent_1`'s output. If the alert is backdated or explicitly non-actionable ("Non-CITO"), it skips further processing and routes directly to the `reporter`. Otherwise, it routes to `agent_2`.
  - **[workflow/agents/agent2.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/agents/agent2.py)**: Intended to run the AI classification. It loads an `AlertClassifier` to evaluate the alert description.
  - **[workflow/classifier/model.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/classifier/model.py)**: Contains the `AlertClassifier` wrapper around a DistilBERT model. It optimizes inference using ONNX Runtime (CPU) and falls back to standard PyTorch if ONNX is missing. It predicts whether an alert is "Auto resolving" or "Non-Auto Resolving".
  - **[workflow/nodes/node_reporter.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/nodes/node_reporter.py)**: Collects the statuses from all agents and emits an overall `success`, `failed`, or `partial_failure` status.

## Data Flow

1. **DNAC** pushes an event to `http://<host>:8000/api/v1/webhook`.
2. **FastAPI (`app/main.py`)** publishes the event to RabbitMQ `dnac.exchange` -> `dnac.alerts.q`.
3. **Consumer (`consumer/noops_dnac_consumer.py`)** consumes the message from `dnac.alerts.q`.
4. **Consumer** maps the JSON to Jenkins parameters and triggers the Jenkins job.
5. **Jenkins** runs `python workflow/run.py --event_id ...`.
6. **LangGraph Pipeline**:
   - `Agent 1` checks for backdated/stale alerts.
   - `Supervisor` evaluates Agent 1. If valid, passes to Agent 2.
   - `Agent 2` runs the NLP DistilBERT model to classify the alert.
   - `Reporter` consolidates results.
7. `run.py` exits with an appropriate exit code and creates `status.json`.

## Observations & Potential Gaps

> [!WARNING]
> Import Path Issue in `node_agent_1.py`
> The import `from workflow.tools.backdate_detector import *` in [node_agent_1.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/nodes/node_agent_1.py#L9) does not match the file structure. The `backdate_detector.py` file is actually located in `workflow/agents/backdate_detector.py`. This will cause an `ImportError` when `run.py` is executed.

> [!NOTE]
> `agent_2` Integration
> The implementation of `agent_2` logic exists in [workflow/agents/agent2.py](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/workflow/agents/agent2.py). However, `workflow/graph/graph.py` currently only binds `agent_1`, `supervisor`, and `reporter` using the nodes in `workflow/nodes/`. The actual `node_agent_2.py` wrapper appears to be missing from the `nodes` folder, and the graph definition does not explicitly attach `agent_2` as a node, although `supervisor` tries to route to `"agent_2"`.

## Summary
The codebase provides a robust, decoupled ingestion and triage flow utilizing state-of-the-art workflow state graphs (LangGraph) and NLP classification (DistilBERT/ONNX). To finalize the pipeline, the import path for `backdate_detector` should be corrected, and the `agent_2` node needs to be fully wired into `graph.py`.
