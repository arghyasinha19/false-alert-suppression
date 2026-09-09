# Coding Conventions

**Analysis Date:** 2026-09-09

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `dnac_client.py`, `backdate_detector.py`, `run_delayed.py`).
- LangGraph nodes: `node_<agent_or_role>.py` (e.g., `node_agent_1.py`, `node_agent_3_scheduler.py`, `node_supervisor.py`).
- React components: `PascalCase.jsx` (e.g., `FalseAlertMetrics.jsx`, `AlertPatterns.jsx`, `ChatPanel.jsx`).
- CSS stylesheets: Match the component name in PascalCase or kebab-case (e.g., `ChatPanel.css`, `App.css`, `index.css`).

**Functions & Methods:**
- Python functions and methods: `snake_case` (e.g., `agent_1_logic`, `evaluate`, `find_incident`, `normalize_json_payload`).
- Private/Internal helper functions: Prefixed with leading underscore (e.g., `_get_classifiers()`, `_build_query()`, `_sanitize_segment()`).
- React handlers and hooks: camelCase (e.g., `fetchData`, `handleSend`, `setActiveView`).

**Variables:**
- Local variables: `snake_case` in Python (e.g., `event_id`, `active_incident`, `predicted_category`), camelCase in JavaScript (e.g., `apiConnected`, `pollInterval`).
- Module constants & Environment settings: `UPPERCASE_WITH_UNDERSCORES` (e.g., `CONFIG_PATH`, `EXIT_CODES`, `API_BASE`, `_REGEX_CASCADE`).

**Types & Classes:**
- Python classes and TypedDicts: `PascalCase` (e.g., `GraphState`, `AgentResult`, `BackdateDecision`, `BackdateDetector`, `MLAlertClassifier`, `MongoDBClient`).
- Custom TypeAliases / Literals: `PascalCase` or uppercase type names (e.g., `Status = Literal["pending", "running", "success", "failed", "skipped"]`).

## Code Style

**Formatting:**
- Python: PEP 8 standard formatting conventions (4-space indentation, 100-120 character soft limit).
- JavaScript/React: ESLint / Oxlint recommended standards with 2-space indentation and single quotes for strings in JSX (`dashboard/.oxlintrc.json`).

**Linting:**
- Frontend: `oxlint` configured via `dashboard/package.json` (`npm run lint`).
- Backend: Standard Python linters (Flake8 / Ruff compatible).

## Import Organization

**Python Import Order:**
1. Standard library imports (e.g., `os`, `sys`, `json`, `logging`, `argparse`, `datetime`, `contextlib`).
2. Third-party packages (e.g., `yaml`, `pika`, `requests`, `fastapi`, `pydantic`, `pymongo`, `langgraph`, `sklearn`, `torch`, `transformers`).
3. Local application imports (e.g., `from workflow.state import GraphState`, `from app.dnac_client import DNACClient`).

**Project Path Anchoring:**
Because scripts are executed from different subdirectories (or triggered via Jenkins), entry points explicitly anchor the project root into `sys.path`:
```python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
```

**Environment Loading:**
Always load `.env` at module import using `find_dotenv()` or project root path to avoid missing variables when executed from subfolders:
```python
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)
```

## Error Handling

**LangGraph Node Exception Isolation:**
Graph nodes must never terminate the process or crash the state machine on an unhandled error. Every node logic function is wrapped using the `safe_node` higher-order function (`workflow/utils/helpers.py`):
```python
def safe_node(agent_name: str, fn: Callable[[GraphState], Dict[str, Any]]):
    def wrapper(state: GraphState) -> GraphState:
        try:
            out = fn(state)
            # update state with success / status
        except Exception as e:
            # record error in state["results"][agent_name]["error"] without raising
            return state
    return wrapper
```

**Fail-Soft Data Fallbacks:**
When external databases or services are unreachable, fallback gracefully rather than raising 500 errors to operators:
```python
def get_alert_records():
    collection = mongo.get_collection("alert_results")
    if collection is not None:
        try:
            alerts = list(collection.find({}, {"_id": 0}))
            if alerts:
                return alerts
        except Exception as e:
            logger.warning(f"MongoDB query failed, falling back to simulated data: {e}")
    return load_simulated_alerts()
```

**Safe Dictionary Extraction:**
Use nested defensive lookups for untrusted network payloads:
```python
def safe_get(d, *keys, default=None):
    curr = d
    for k in keys:
        if not isinstance(curr, dict):
            return default
        curr = curr.get(k)
        if curr is None:
            return default
    return curr
```

## Logging

**Framework:** Python standard library `logging`.

**Patterns:**
- Always instantiate named loggers rather than root logger:
  ```python
  logger = logging.getLogger(__name__)
  ```
- Prefix log statements with the alert identifier for distributed tracing:
  ```python
  logger.info(f"[{event_id}] Entering Agent 2. Input payload: {alert}")
  ```
- Use `exc_info=True` or `logger.exception()` inside except blocks:
  ```python
  logger.error(f"[{event_id}] Agent 2 classification failed: {e}", exc_info=True)
  ```
- Silence third-party noise (Hugging Face, PyTorch, urllib3) in Jenkins runners:
  ```python
  for name in ["transformers", "torch", "urllib3"]:
      logging.getLogger(name).setLevel(logging.ERROR)
  ```

## Comments & Docstrings

**When to Comment:**
- Header docstrings on entry points explaining purpose, inputs, and Jenkins integration.
- Clear inline comments explaining business logic gates (e.g., why 24 hours skew is considered backdated, why a 15-minute wait queue is scheduled).
- Documenting why mock/fallback paths exist.

**Example Pattern:**
```python
def agent_1_logic(state: GraphState) -> Dict[str, Any]:
    """
    Agent 1 is responsible for identifying if an alert is backdated or not.
    If an alert timestamp is older than the configured threshold (24 hours),
    this agent flags it to prevent tickets on historical noise.
    """
```

## Function & Module Design

**Single Responsibility:**
- Each node file in `workflow/nodes/` contains a single node logic function receiving `state: GraphState` and returning a dictionary update.
- External interaction details (API calls, SQL/NoSQL queries, RabbitMQ pushes) are encapsulated in `workflow/tools/` classes.

**Stateless Logic:**
- Node functions compute output purely based on `state["alert"]` and prior node results in `state["results"]`.

---

*Convention analysis: 2026-09-09*
