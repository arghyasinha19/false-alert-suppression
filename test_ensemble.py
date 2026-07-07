import os
import sys
import logging
import time

# Ensure we can import from workflow
sys.path.append(os.path.dirname(__file__))

from workflow.nodes.node_agent_2 import agent_2_logic

logging.basicConfig(level=logging.INFO)

def run_test():
    # Test 1: Easy alert (should be classified by ML_TFIDF with high confidence)
    state = {
        "alert": {
            "event_id": "TEST_1",
            "description": "ThousandEyes Alert triggered for [underlay] - UK Hub Primary"
        },
        "results": {}
    }
    print("Running Test 1 (Easy ML Match)...")
    res1 = agent_2_logic(state)
    print(res1)
    print("-" * 50)
    
    # Test 2: Unseen / Weird alert (might fall back to DL_DISTILBERT if ML is unsure)
    # Actually ML might be sure it's uncertain if we give it completely random text.
    state2 = {
        "alert": {
            "event_id": "TEST_2",
            "description": "Some completely weird failure on random-device.corp"
        },
        "results": {}
    }
    print("Running Test 2 (Potential DL Fallback)...")
    res2 = agent_2_logic(state2)
    print(res2)
    print("-" * 50)

if __name__ == "__main__":
    run_test()
