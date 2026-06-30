import os, sys
import logging
import yaml

from workflow.state import GraphState
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MockClassifier:
    def predict(self, text):
        return {"category": "Auto resolving", "confidence": 0.92, "label_id": 1}

# Module-level classifier singleton
_classifier = None
_classifier_load_attempted = False

def _get_classifier():
    global _classifier, _classifier_load_attempted
    
    if _classifier is not None:
        return _classifier
        
    if _classifier_load_attempted:
        return None
        
    _classifier_load_attempted = True
    
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config.yaml",
        )
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
        model_path = config.get("classifier", {}).get("model_path", "models")
        # Ensure model_path is relative to the project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if not os.path.isabs(model_path):
            model_path = os.path.join(project_root, model_path)
        
        from workflow.classifier.model import AlertClassifier
        
        _classifier = AlertClassifier.load(model_path)
        logger.info(f"Agent 2: Classifier loaded from {model_path}")
        return _classifier
        
    except FileNotFoundError:
        logger.warning("Agent 2: No trained model found. Using mock classifier for testing.")
        _classifier = MockClassifier()
        return _classifier

def agent_2_logic(state: GraphState) -> Dict[str, Any]:
    """
    Agent 2 is responsible for classifying the alert as Auto resolving or Non-Auto Resolving.
    """
    alert = state.get("alert", {})
    event_id = alert.get("event_id", "UNKNOWN")
    logger.info(f"[{event_id}] Entering Agent 2. Input payload: {alert}")
    
    agent1_data = state.get("results", {}).get("agent_1", {}).get("data", {})
    
    # Extract description
    description = (
        agent1_data.get("description")
        or alert.get("issue_details", "")
        or alert.get("issue_name", "")
        or alert.get("description", "")
        or alert.get("details", {}).get("description", "")
        or alert.get("name", "")
    )
    
    description = str(description).strip()
    
    if not description:
        return {
            "ok": False,
            "data": None,
            "remarks": "skipped: no description found for classification"
        }
        
    classifier = _get_classifier()
    if classifier is None:
        return {
            "ok": False,
            "data": None,
            "remarks": "skipped: classifier not loaded"
        }
        
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config.yaml",
        )
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
        threshold = config.get("classifier", {}).get("confidence_threshold", 0.6)
        
        result = classifier.predict(description)
        
        if result["confidence"] >= threshold:
            final_category = result["category"]
        else:
            final_category = "uncertain"
            
        data = {
            "predicted_category": final_category,
            "raw_prediction": result["category"],
            "confidence": result["confidence"],
            "label_id": result["label_id"],
            "threshold_applied": threshold,
        }
        
        logger.info(f"[{event_id}] Agent 2 classified alert | prediction={final_category} | confidence={result['confidence']:.4f}")
        
        output = {
            "ok": True,
            "data": data,
            "remarks": "successfully classified"
        }
        logger.info(f"[{event_id}] Agent 2 completed. Output: {output}")
        return output
        
    except Exception as e:
        logger.error(f"[{event_id}] Agent 2 classification failed: {e}", exc_info=True)
        return {
            "ok": False,
            "data": None,
            "remarks": f"error: {str(e)}"
        }
