"""Unit tests for the shared DNAC status check (workflow/tools/dnac_status.py)."""
import os
import sys
import unittest
from unittest.mock import MagicMock

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from workflow.tools.dnac_status import check_alert_status, ACTIVE, RESOLVED, UNCERTAIN


def _client(primary="NOT_FOUND", by_status=None, raise_on_scan=False):
    c = MagicMock()
    c.get_issue_status.return_value = primary
    by_status = by_status or {}

    def _issues(device_id=None, issue_status=None, **_):
        if raise_on_scan:
            raise RuntimeError("DNAC down")
        return by_status.get(issue_status, [])
    c.get_device_issues.side_effect = _issues
    return c


class TestDNACStatus(unittest.TestCase):

    def test_primary_active(self):
        c = _client(primary="ACTIVE")
        self.assertEqual(check_alert_status(issue_id="ISS-1", device_id="D1", client=c), ACTIVE)
        c.get_issue_status.assert_called_once_with("ISS-1")
        c.get_device_issues.assert_not_called()

    def test_primary_resolved_and_ignored(self):
        for st in ("RESOLVED", "IGNORED"):
            c = _client(primary=st)
            self.assertEqual(check_alert_status(issue_id="ISS-1", device_id="D1", client=c), RESOLVED)

    def test_fallback_matches_by_issue_id(self):
        c = _client(primary="UNSUPPORTED", by_status={
            "RESOLVED": [{"issueId": "ISS-9", "name": "something else", "deviceId": "D1"}]})
        self.assertEqual(check_alert_status(issue_id="ISS-9", device_id="D1", client=c), RESOLVED)

    def test_fallback_matches_by_name_on_same_device(self):
        c = _client(by_status={"ACTIVE": [{"issueId": "X", "name": "Interface Gi1/0/1 is down", "deviceId": "D1"}]})
        self.assertEqual(
            check_alert_status(device_id="D1", issue_name="interface gi1/0/1 is down", client=c), ACTIVE)

    def test_no_device_id_is_uncertain_not_resolved(self):
        c = _client()
        self.assertEqual(check_alert_status(device_name="sw1", issue_name="x", client=c), UNCERTAIN)
        c.get_device_issues.assert_not_called()

    def test_dnac_error_is_uncertain(self):
        c = _client(primary="NOT_FOUND", raise_on_scan=True)
        self.assertEqual(check_alert_status(issue_id="I", device_id="D1", issue_name="x", client=c), UNCERTAIN)

    def test_primary_exception_falls_back(self):
        c = _client(by_status={"ACTIVE": [{"issueId": "I", "name": "n", "deviceId": "D1"}]})
        c.get_issue_status.side_effect = RuntimeError("timeout")
        self.assertEqual(check_alert_status(issue_id="I", device_id="D1", client=c), ACTIVE)

    def test_no_match_is_uncertain(self):
        c = _client(by_status={"RESOLVED": [{"issueId": "Z", "name": "Fan failure", "deviceId": "D1"}]})
        self.assertEqual(check_alert_status(device_id="D1", issue_name="BGP peer down", client=c), UNCERTAIN)


if __name__ == "__main__":
    unittest.main()
