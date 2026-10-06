"""
Regression tests for the production-readiness fixes.
Run:  python -m pytest tests/test_prod_hardening.py -q
All external systems (DNAC, RabbitMQ, ServiceNow, MongoDB, SMTP) are mocked.
"""
import os
import sys
import time
import importlib
from unittest.mock import MagicMock, patch

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault("DNAC_USERNAME", "u")
os.environ.setdefault("DNAC_PASSWORD", "p")
os.environ.setdefault("RABBITMQ_USERNAME", "u")
os.environ.setdefault("RABBITMQ_PASSWORD", "p")


# ---------------------------------------------------------------------------
# Fixtures / fakes
# ---------------------------------------------------------------------------
class FakeSnow:
    """In-memory stand-in for ServiceNowClient."""
    instances = []

    def __init__(self, fail_lookup=False, open_inc=None, resolved_inc=None, by_corr=None):
        self.fail_lookup = fail_lookup
        self.open_inc = open_inc
        self.resolved_inc = resolved_inc
        self.by_corr = by_corr
        self.created = []
        self.comments = []
        self.reopened = []
        self.configured = True
        FakeSnow.instances.append(self)

    def _maybe_fail(self):
        if self.fail_lookup:
            from workflow.tools.servicenow_client import ServiceNowError
            raise ServiceNowError("SNOW down")

    def find_by_correlation_id(self, cid):
        self._maybe_fail()
        return self.by_corr

    def find_open_incident(self, device):
        self._maybe_fail()
        return self.open_inc

    def find_recently_resolved_incident(self, device, days):
        self._maybe_fail()
        return self.resolved_inc

    def find_recently_closed_incident(self, device, days):
        self._maybe_fail()
        return None

    def append_comment(self, sys_id, text):
        self.comments.append(sys_id)

    def reopen_incident(self, sys_id, text):
        self.reopened.append(sys_id)

    def create_incident(self, device, issue, raw, **kw):
        self.created.append((device, kw.get("correlation_id")))
        return {"number": "INC0001", "sys_id": "abc"}


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    """No Mongo, no SMTP, deterministic classifier, SNOW push enabled."""
    import workflow.nodes.node_reporter as rep
    fake_mongo = MagicMock()
    monkeypatch.setattr(rep, "MongoDBClient", lambda: fake_mongo)
    import workflow.tools.email_client as ec
    monkeypatch.setattr(ec.EmailClient, "send_email", lambda self, s, b: True)
    monkeypatch.setenv("SNOW_PUSH_ENABLED", "yes")
    FakeSnow.instances.clear()
    yield fake_mongo


class FixedClassifier:
    def __init__(self, category, confidence=0.95):
        self.category, self.confidence = category, confidence

    def predict(self, text):
        return {"category": self.category, "confidence": self.confidence, "label_id": 0}


def _set_classifier(monkeypatch, ml, dl=None):
    import workflow.nodes.node_agent_2 as a2
    monkeypatch.setattr(a2, "_classifiers_load_attempted", True)
    monkeypatch.setattr(a2, "_ml_classifier", ml)
    monkeypatch.setattr(a2, "_dl_classifier", dl)


def _use_snow(monkeypatch, snow):
    import workflow.nodes.node_agent_4_servicenow as a4
    monkeypatch.setattr(a4, "ServiceNowClient", lambda: snow)


def _alert(**kw):
    a = dict(event_id="NETWORK-DEVICES-3-506", instance_id="inst-1", device_id="D1",
             device_name="sw1", raw_timestamp=str(int(time.time() * 1000)),
             issue_name="Interface down", issue_details="Interface Gi1/0/1 is down",
             status="active")
    a.update(kw)
    return a


def _run(alert):
    from workflow.graph import build_graph
    return build_graph().invoke({"alert": alert, "results": {}, "errors": [], "remarks": {}})


# ---------------------------------------------------------------------------
# DNAC client
# ---------------------------------------------------------------------------
def test_extract_issue_id_from_event_link():
    from app.dnac_client import extract_issue_id
    ev = {"instanceId": "inst", "ciscoDnaEventLink": "https://dnac/dna/assurance/issueDetails?issueId=abc-123"}
    assert extract_issue_id(ev) == "abc-123"
    assert extract_issue_id({"instanceId": "x"}) is None


def _resp(status=200, json_body=None, text=""):
    r = MagicMock()
    r.status_code = status
    r.ok = 200 <= status < 300
    r.json.return_value = json_body if json_body is not None else {}
    r.text = text or str(json_body)
    return r


def test_device_issues_uses_deviceId_and_refuses_unfiltered():
    from app.dnac_client import DNACClient
    c = DNACClient({"base_url": "https://dnac"})
    c.token = "t"
    with patch("app.dnac_client.requests.request", return_value=_resp(200, {"response": []})) as req:
        c.get_device_issues(device_id="D1", device_name="sw1", issue_status="active")
        params = req.call_args.kwargs["params"]
        assert params == {"deviceId": "D1", "issueStatus": "ACTIVE"}
        assert "timeout" in req.call_args.kwargs
        req.reset_mock()
        assert c.get_device_issues(device_name="sw1") == []
        req.assert_not_called()


def test_issue_status_uses_assurance_issue_endpoint():
    from app.dnac_client import DNACClient
    c = DNACClient({"base_url": "https://dnac"})
    c.token = "t"
    with patch("app.dnac_client.requests.request",
               return_value=_resp(200, {"response": {"issueId": "I1", "status": "resolved"}})) as req:
        assert c.get_issue_status("I1") == "RESOLVED"
        assert req.call_args.args[1].endswith("/dna/data/api/v1/assuranceIssues/I1")


def test_device_health_is_device_specific():
    from app.dnac_client import DNACClient
    c = DNACClient({"base_url": "https://dnac"})
    c.token = "t"
    detail = {"response": {"overallHealth": 8, "cpu": 12.5, "memory": 40.0, "communicationState": "REACHABLE"}}
    inv = {"response": {"reachabilityStatus": "Reachable"}}
    with patch("app.dnac_client.requests.request", side_effect=[_resp(200, detail), _resp(200, inv)]) as req:
        h = c.get_device_health("UUID-1")
        first = req.call_args_list[0]
        assert first.args[1].endswith("/dna/intent/api/v1/device-detail")
        assert first.kwargs["params"] == {"identifier": "uuid", "searchBy": "UUID-1"}
        assert h["health_score"] == 8 and h["cpu"] == 12.5 and h["reachable"] is True


# ---------------------------------------------------------------------------
# Main workflow: fail-safe escalation
# ---------------------------------------------------------------------------
def test_missing_description_does_not_crash_and_escalates(monkeypatch):
    _set_classifier(monkeypatch, FixedClassifier("Auto resolving"))
    snow = FakeSnow()
    _use_snow(monkeypatch, snow)
    s = _run(_alert(issue_details=None, issue_name=None))
    assert s["results"]["agent_2"]["status"] == "failed"
    assert s["results"]["agent_4"]["data"]["action"] == "incident_created"
    assert snow.created


def test_missing_model_escalates_instead_of_mock(monkeypatch):
    monkeypatch.delenv("ALLOW_MOCK_CLASSIFIER", raising=False)
    _set_classifier(monkeypatch, None, None)
    snow = FakeSnow()
    _use_snow(monkeypatch, snow)
    s = _run(_alert())
    assert s["results"]["agent_2"]["ok"] is False
    assert snow.created, "alert must be escalated when no classifier is loaded"


def test_delay_queue_failure_escalates(monkeypatch):
    _set_classifier(monkeypatch, FixedClassifier("Auto resolving"))
    import workflow.nodes.node_agent_3_scheduler as a3
    monkeypatch.setattr(a3.RabbitMQBroker, "publish_delayed_message", lambda self, p: False)
    snow = FakeSnow()
    _use_snow(monkeypatch, snow)
    s = _run(_alert())
    assert s["results"]["agent_3"]["status"] == "failed"
    assert s["results"]["agent_4"]["data"]["action"] == "incident_created"


def test_auto_resolving_scheduled_is_not_ticketed(monkeypatch):
    _set_classifier(monkeypatch, FixedClassifier("Auto resolving"))
    import workflow.nodes.node_agent_3_scheduler as a3
    monkeypatch.setattr(a3.RabbitMQBroker, "publish_delayed_message", lambda self, p: True)
    snow = FakeSnow()
    _use_snow(monkeypatch, snow)
    s = _run(_alert())
    assert s["results"]["agent_4"]["status"] == "skipped"
    assert not snow.created
    assert s["overall_status"] == "success"


def test_resolution_notification_never_touches_snow(monkeypatch):
    _set_classifier(monkeypatch, FixedClassifier("Non-Auto Resolving"))
    snow = FakeSnow()
    _use_snow(monkeypatch, snow)
    s = _run(_alert(status="resolved"))
    assert "agent_4" not in s["results"]
    assert "resolution_notification" in s["results"]["agent_2"]["reason"]


def test_missing_timestamp_is_not_suppressed(monkeypatch):
    _set_classifier(monkeypatch, FixedClassifier("Non-Auto Resolving"))
    snow = FakeSnow()
    _use_snow(monkeypatch, snow)
    s = _run(_alert(raw_timestamp=None))
    assert s["results"]["agent_1"]["data"]["is_backdated"] is False
    assert snow.created


def test_backdated_alert_still_suppressed(monkeypatch):
    _set_classifier(monkeypatch, FixedClassifier("Non-Auto Resolving"))
    snow = FakeSnow()
    _use_snow(monkeypatch, snow)
    old = str(int((time.time() - 3 * 86400) * 1000))
    s = _run(_alert(raw_timestamp=old))
    assert s["results"]["agent_1"]["data"]["is_backdated"] is True
    assert not snow.created


# ---------------------------------------------------------------------------
# ServiceNow behaviour
# ---------------------------------------------------------------------------
def test_snow_lookup_failure_fails_loudly_and_does_not_create(monkeypatch):
    _set_classifier(monkeypatch, FixedClassifier("Non-Auto Resolving"))
    snow = FakeSnow(fail_lookup=True)
    _use_snow(monkeypatch, snow)
    s = _run(_alert())
    assert s["results"]["agent_4"]["status"] == "failed"
    assert not snow.created
    assert s["overall_status"] in ("failed", "partial_failure")


def test_snow_idempotent_on_redelivery(monkeypatch):
    _set_classifier(monkeypatch, FixedClassifier("Non-Auto Resolving"))
    snow = FakeSnow(by_corr={"number": "INC0009", "sys_id": "z"})
    _use_snow(monkeypatch, snow)
    s = _run(_alert())
    assert s["results"]["agent_4"]["data"]["action"] == "duplicate_event_ignored"
    assert not snow.created


def test_snow_device_match_is_exact():
    from workflow.tools.servicenow_client import ServiceNowClient
    same = ServiceNowClient._is_same_device
    assert same({"short_description": "Monitoring Alert: sw1"}, "sw1")
    assert same({"short_description": "Monitoring Alert: sw1 - Interface down"}, "sw1")
    assert not same({"short_description": "Monitoring Alert: sw10"}, "sw1")


def test_snow_unconfigured_raises():
    from workflow.tools.servicenow_client import ServiceNowClient, ServiceNowError
    with patch.dict(os.environ, {"SNOW_INSTANCE_URL": ""}):
        with pytest.raises(ServiceNowError):
            ServiceNowClient().find_open_incident("sw1")


# ---------------------------------------------------------------------------
# Delayed flow
# ---------------------------------------------------------------------------
def test_delayed_resolved_records_results(monkeypatch, _isolate):
    import workflow.delayed as d
    monkeypatch.setattr(d, "check_alert_status", lambda **k: "RESOLVED")
    snow = FakeSnow()
    _use_snow(monkeypatch, snow)
    s = d.run_delayed_check(_alert())
    assert s["alert"]["event_id"] == "NETWORK-DEVICES-3-506"
    assert s["results"]["delayed_check"]["data"]["dnac_status"] == "RESOLVED"
    assert s["overall_status"] == "success"
    assert not snow.created
    # merge mode: only results.<key> written, main-run results preserved
    payload = _isolate.save_alert_result.call_args.args[1]
    assert "results" not in payload and "results.delayed_check" in payload


def test_delayed_active_and_uncertain_escalate(monkeypatch):
    import workflow.delayed as d
    for st in ("ACTIVE", "UNCERTAIN"):
        monkeypatch.setattr(d, "check_alert_status", lambda **k: st)
        snow = FakeSnow()
        _use_snow(monkeypatch, snow)
        s = d.run_delayed_check(_alert())
        assert s["results"]["agent_4"]["data"]["action"] == "incident_created", st
        assert s["overall_status"] == "success"


# ---------------------------------------------------------------------------
# Webhook ingestion
# ---------------------------------------------------------------------------
@pytest.fixture
def ingest(monkeypatch):
    monkeypatch.setenv("WEBHOOK_AUTH_TOKEN", "secret")
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED_WEBHOOK", raising=False)
    import app.main as m
    m = importlib.reload(m)
    m.mq_publisher.publish = MagicMock()
    from fastapi.testclient import TestClient
    return m, TestClient(m.app)


def test_webhook_requires_token(ingest):
    m, client = ingest
    assert client.post("/api/v1/webhook", json={"eventId": "x"}).status_code == 401
    r = client.post("/api/v1/webhook", json={"eventId": "x"}, headers={"X-Webhook-Token": "secret"})
    assert r.status_code == 200


def test_webhook_adds_issue_id_and_received_at(ingest):
    m, client = ingest
    ev = {"eventId": "x", "ciscoDnaEventLink": "https://dnac/x?issueId=ISS-7"}
    client.post("/api/v1/webhook", json=ev, headers={"X-Webhook-Token": "secret"})
    sent = m.mq_publisher.publish.call_args.args[0]
    assert sent["issueId"] == "ISS-7" and sent["_received_at"]


def test_webhook_returns_503_when_publish_fails(ingest):
    m, client = ingest
    m.mq_publisher.publish.side_effect = RuntimeError("unroutable")
    r = client.post("/api/v1/webhook", json=[{"eventId": "a"}], headers={"X-Webhook-Token": "secret"})
    assert r.status_code == 503


def test_subscription_endpoints_require_admin(ingest):
    m, client = ingest
    assert client.get("/api/v1/subscriptions").status_code == 401


# ---------------------------------------------------------------------------
# Static checks
# ---------------------------------------------------------------------------
def test_jenkinsfiles_do_not_interpolate_params_into_shell():
    for name in ("Jenkinsfile.main", "Jenkinsfile.delayed"):
        text = open(os.path.join(ROOT, "jenkins", name), encoding="utf-8").read()
        assert "${params." not in text, name
        assert 'sh """' not in text, name


def test_no_hardcoded_rabbitmq_password():
    text = open(os.path.join(ROOT, "consumer", "config", "rabbitmq.py"), encoding="utf-8").read()
    assert "JustCheck" not in text
