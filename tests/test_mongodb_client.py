import os
import sys
from unittest.mock import MagicMock

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from workflow.tools.mongodb_client import MongoDBClient


def test_save_alert_result_generates_unique_instance_id_when_missing():
    client = MongoDBClient.__new__(MongoDBClient)
    client.db = MagicMock()
    mock_coll = MagicMock()
    mock_coll.index_information.return_value = {}
    client.get_collection = MagicMock(return_value=mock_coll)

    # Payload without instance_id or raw_timestamp
    payload1 = {
        "alert_details": {
            "device_id": "dev-001",
            "device_name": "Switch-01",
        },
        "results": {"agent_1": {"status": "success"}},
    }
    res1 = client.save_alert_result("EVT-100", payload1)
    assert res1 is True
    assert mock_coll.update_one.call_count == 1
    call1_filter, call1_update = mock_coll.update_one.call_args[0]
    
    inst1 = call1_filter["alert_details.instance_id"]
    raw_ts1 = call1_filter["alert_details.raw_timestamp"]
    assert inst1 is not None and inst1.startswith("inst-")
    assert raw_ts1 is not None and isinstance(raw_ts1, int)
    assert payload1["alert_id"] == "EVT-100"

    # Second alert for the exact same event and device without instance_id
    payload2 = {
        "alert_details": {
            "device_id": "dev-001",
            "device_name": "Switch-01",
        },
        "results": {"agent_1": {"status": "success"}},
    }
    res2 = client.save_alert_result("EVT-100", payload2)
    assert res2 is True
    assert mock_coll.update_one.call_count == 2
    call2_filter, call2_update = mock_coll.update_one.call_args[0]
    
    inst2 = call2_filter["alert_details.instance_id"]
    # Verify inst1 != inst2 so they do not collide / overwrite!
    assert inst1 != inst2


def test_save_alert_result_preserves_explicit_instance_id_for_delayed_update():
    client = MongoDBClient.__new__(MongoDBClient)
    client.db = MagicMock()
    mock_coll = MagicMock()
    mock_coll.index_information.return_value = {}
    client.get_collection = MagicMock(return_value=mock_coll)

    payload = {
        "alert_details": {
            "instance_id": "inst-fixed-12345",
            "device_id": "dev-002",
            "raw_timestamp": 1784691600000,
        },
        "results.delayed_check": {"status": "success"},
    }
    res = client.save_alert_result("EVT-200", payload)
    assert res is True
    filter_arg, _ = mock_coll.update_one.call_args[0]
    assert filter_arg["alert_details.instance_id"] == "inst-fixed-12345"
    assert filter_arg["alert_details.raw_timestamp"] == 1784691600000


def test_ensure_indexes_drops_legacy_unique_index():
    client = MongoDBClient.__new__(MongoDBClient)
    mock_coll = MagicMock()
    mock_coll.index_information.return_value = {
        "alert_id_1": {"unique": True, "key": [("alert_id", 1)]},
        "dedup_composite_key": {"unique": True, "key": [("alert_id", 1)]},
    }
    client.get_collection = MagicMock(return_value=mock_coll)

    client._ensure_indexes()
    # Check that drop_index was called for alert_id_1 and dedup_composite_key
    mock_coll.drop_index.assert_any_call("alert_id_1")
    mock_coll.drop_index.assert_any_call("dedup_composite_key")
    # And create_index was called with background=True without unique=True
    mock_coll.create_index.assert_called_once()
    assert mock_coll.create_index.call_args[1].get("unique") is not True
