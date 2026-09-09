# Testing Patterns

**Analysis Date:** 2026-09-09

## Test Framework

**Runner:**
- Python standard library `unittest`
- Standalone executable test/diagnostic scripts (`test_*.py`)

**Assertion Library:**
- `unittest.TestCase` assertions (`self.assertIs`, `self.assertEqual`, `self.assertTrue`)

**Run Commands:**
```bash
# Run all unit tests via standard discovery
python -m unittest discover -s . -p "test_*.py"

# Run specific unit test suites
python -m unittest test_dnac_fallback.py

# Run standalone verification scripts
python test_payload_extraction.py
python test_ensemble.py
python test_rmq.py
```

## Test File Organization

**Location:**
- Tests and verification scripts currently reside primarily in the root directory alongside the solution files (`test_dnac_fallback.py`, `test_payload_extraction.py`, `test_ensemble.py`, `test_rmq.py`).
- Dedicated synthetic datasets and test payloads are located in `data/` (`data/auto_resolving_alerts.json`, `data/non_auto_resolving_alerts.json`, `data/backdated_alerts.json`, `data/simulated_alerts.json`).

**Naming:**
- Unit test files: `test_<module_or_feature>.py`
- Test classes: `Test<FeatureName>(unittest.TestCase)`
- Test methods: `test_<scenario_or_condition>`

**Structure:**
```
false-alert-suppression/
├── test_dnac_fallback.py          # Unit tests with mocks for DNAC status fallback logic
├── test_ensemble.py               # Functional test for TF-IDF vs DistilBERT classification
├── test_payload_extraction.py     # Schema validation against actual production payloads
├── test_rmq.py                    # RabbitMQ queue and delay configuration validation
└── data/                          # Ground-truth test fixtures and simulated alert pools
```

## Test Structure

**Suite Organization (`unittest`):**
```python
import unittest
from unittest.mock import patch, MagicMock
from workflow.run_delayed import check_dnac_status

class TestDNACStatusFallback(unittest.TestCase):

    @patch("app.dnac_client.DNACClient")
    def test_primary_active(self, mock_dnac_cls):
        mock_client = MagicMock()
        mock_client.get_issue_status.return_value = "ACTIVE"
        mock_dnac_cls.return_value = mock_client

        res = check_dnac_status(
            instance_id="INST-100",
            device_id="DEV-001",
            device_name="switch-01",
            issue_name="Interface Down"
        )
        self.assertIs(res, True)
        mock_client.get_issue_status.assert_called_once_with("INST-100")
```

## Mocking

**Framework:**
- `unittest.mock` (`patch`, `MagicMock`)
- Custom in-memory fallback mock classes (`MockClassifier` in `workflow/nodes/node_agent_2.py`)

**Patterns:**
- Mocking external network boundaries (Cisco DNAC REST API, ServiceNow Table API, RabbitMQ broker):
  ```python
  @patch("app.dnac_client.DNACClient")
  def test_fallback_active_matching(self, mock_dnac_cls):
      mock_client = MagicMock()
      mock_client.get_issue_status.return_value = "NOT_FOUND"
      mock_client.get_device_issues.return_value = [{"issueId": "123", "issueStatus": "ACTIVE"}]
      mock_dnac_cls.return_value = mock_client
      ...
  ```
- Graceful in-memory mock classifier when ML weights are unavailable:
  ```python
  class MockClassifier:
      def predict(self, text):
          return {"category": "Auto resolving", "confidence": 0.92, "label_id": 1}
  ```

**What to Mock:**
- External appliance HTTP calls (Cisco DNAC tokens, ServiceNow incidents).
- RabbitMQ network connections during unit tests.
- Heavy PyTorch / Transformer model loading during lightweight unit tests.

**What NOT to Mock:**
- LangGraph state routing and supervisor conditional transitions.
- Regex extraction and payload normalization functions (`normalize_json_payload`, `BackdateDetector`).
- Scikit-learn TF-IDF pipeline predictions when verifying inference latency.

## Fixtures and Factories

**Test Data:**
- Production payload snapshot transcribed from appliance UI (`test_payload_extraction.py:32`):
  ```python
  DNAC_PAYLOAD = {
      "version": "1.0.0",
      "instanceId": "39c901fa-b130-499c-836d-017da0f5de7f",
      "eventId": "NETWORK-DEVICES-2-119",
      "severity": 2,
      "details": {
          "Type": "Network Device",
          "Assurance Issue Details": "AP(s) are disconnected from Wireless Controller...",
          "Device": "UK-MAL-DEV-AS01.dyson.global.corp",
          "Assurance Issue Status": "active"
      }
  }
  ```
- Pre-generated synthetic alert corpus (`data/simulated_alerts.json`).
- Dynamic test alert generator in `simulate_data.py`:
  ```python
  alerts = generate_simulated_alerts(count=60)
  ```

## Coverage

**Requirements:**
- No strict percentage enforced by CI yet.
- Core business logic (backdate detection, classification routing, delay queue scheduling, ServiceNow incident deduplication) must have regression coverage.

## Test Types

**Unit Tests:**
- Fast tests with zero external dependencies.
- Example: `test_dnac_fallback.py` testing the 3-stage fallback resolution in `check_dnac_status()`.

**Integration & Contract Tests:**
- Validate field mapping against real Cisco DNAC schemas.
- Example: `test_payload_extraction.py` checking that `eventId`, `device_name`, and nested `details` map accurately to consumer payloads.

**End-to-End Simulation Tests:**
- Simulating alert streams into RabbitMQ.
- Example: `inject_to_rabbitmq.py` pushing test events to verify consumer processing through to Jenkins and MongoDB.

---

*Testing analysis: 2026-09-09*
