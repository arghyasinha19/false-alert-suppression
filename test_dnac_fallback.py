import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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

    @patch("app.dnac_client.DNACClient")
    def test_primary_resolved(self, mock_dnac_cls):
        mock_client = MagicMock()
        mock_client.get_issue_status.return_value = "RESOLVED"
        mock_dnac_cls.return_value = mock_client

        res = check_dnac_status(
            instance_id="INST-101",
            device_id="DEV-001",
            device_name="switch-01",
            issue_name="Interface Down"
        )
        self.assertIs(res, False)
        mock_client.get_issue_status.assert_called_once_with("INST-101")

    @patch("app.dnac_client.DNACClient")
    def test_fallback_active_matching(self, mock_dnac_cls):
        mock_client = MagicMock()
        # Primary lookup returns NOT_FOUND (404)
        mock_client.get_issue_status.return_value = "NOT_FOUND"
        # Device active issues lookup returns matching active issue
        mock_client.get_device_issues.side_effect = lambda device_id, device_name, issue_status: [
            {
                "issueId": "INST-NEW-99",
                "name": "Interface GigabitEthernet1/0/1 is down",
                "issueStatus": "ACTIVE"
            }
        ] if issue_status == "ACTIVE" else []

        mock_dnac_cls.return_value = mock_client

        res = check_dnac_status(
            instance_id="INST-404-OLD",
            device_id="DEV-001",
            device_name="switch-01",
            issue_name="Interface GigabitEthernet1/0/1 is down"
        )
        self.assertIs(res, True)

    @patch("app.dnac_client.DNACClient")
    def test_fallback_resolved_matching(self, mock_dnac_cls):
        mock_client = MagicMock()
        # Primary lookup returns NOT_FOUND (404)
        mock_client.get_issue_status.return_value = "NOT_FOUND"
        # Active issues returns empty / non-matching, Resolved issues returns matching resolved issue
        def mock_get_device_issues(device_id, device_name, issue_status):
            if issue_status == "ACTIVE":
                return []
            elif issue_status == "RESOLVED":
                return [
                    {
                        "issueId": "INST-RESOLVED-88",
                        "name": "Interface GigabitEthernet1/0/1 is down",
                        "issueStatus": "RESOLVED"
                    }
                ]
            return []

        mock_client.get_device_issues.side_effect = mock_get_device_issues
        mock_dnac_cls.return_value = mock_client

        res = check_dnac_status(
            instance_id="INST-404-OLD",
            device_id="DEV-001",
            device_name="switch-01",
            issue_name="Interface GigabitEthernet1/0/1 is down"
        )
        self.assertIs(res, False)

    @patch("app.dnac_client.DNACClient")
    def test_fallback_uncertain(self, mock_dnac_cls):
        mock_client = MagicMock()
        # Primary lookup returns NOT_FOUND (404)
        mock_client.get_issue_status.return_value = "NOT_FOUND"
        # Both active and resolved lookups return no matching issues
        mock_client.get_device_issues.return_value = []
        mock_dnac_cls.return_value = mock_client

        res = check_dnac_status(
            instance_id="INST-404-MISSING",
            device_id="DEV-001",
            device_name="switch-01",
            issue_name="Unrelated High Memory Usage Alert"
        )
        self.assertEqual(res, "Uncertain")


if __name__ == "__main__":
    unittest.main()
