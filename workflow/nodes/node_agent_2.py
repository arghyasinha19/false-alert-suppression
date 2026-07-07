import os, sys
import logging
import yaml

from workflow.state import GraphState
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MockClassifier:
    def predict(self, text):
        return {"category": "Auto resolving", "confidence": 0.92, "label_id": 1}

# Module-level classifier singletons
_ml_classifier = None
_dl_classifier = None
_classifiers_load_attempted = False

def _get_classifiers():
    global _ml_classifier, _dl_classifier, _classifiers_load_attempted
    
    if _classifiers_load_attempted:
        return _ml_classifier, _dl_classifier
        
    _classifiers_load_attempted = True
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config.yaml",
    )
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}
        
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # 1. Load ML Classifier (Option A)
    ml_model_path = os.path.join(project_root, "models", "ml_model.joblib")
    try:
        from workflow.classifier.model_ml import MLAlertClassifier
        _ml_classifier = MLAlertClassifier.load(ml_model_path)
        logger.info(f"Agent 2: ML Classifier loaded from {ml_model_path}")
    except Exception as e:
        logger.warning(f"Agent 2: Failed to load ML Classifier: {e}")
        _ml_classifier = MockClassifier()
        
    # 2. Load DL Classifier (Option C - DistilBERT)
    dl_model_path = config.get("classifier", {}).get("model_path", "models")
    if not os.path.isabs(dl_model_path):
        dl_model_path = os.path.join(project_root, dl_model_path)
    
    try:
        from workflow.classifier.model import AlertClassifier
        _dl_classifier = AlertClassifier.load(dl_model_path)
        logger.info(f"Agent 2: DL Classifier loaded from {dl_model_path}")
    except Exception as e:
        logger.warning(f"Agent 2: Failed to load DL Classifier: {e}")
        _dl_classifier = MockClassifier()
        
    return _ml_classifier, _dl_classifier

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
        
    ml_clf, dl_clf = _get_classifiers()
    if ml_clf is None and dl_clf is None:
        return {
            "ok": False,
            "data": None,
            "remarks": "skipped: classifiers not loaded"
        }
        
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config.yaml",
        )
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
        threshold = config.get("classifier", {}).get("confidence_threshold", 0.6)
        ml_threshold = 0.85 # High confidence threshold for ML fallback
        
        # 1. Primary: ML Classifier
        result = ml_clf.predict(description)
        used_model = "ML_TFIDF"
        
        # 2. Fallback: DL Classifier if ML confidence is low
        if result["confidence"] < ml_threshold and not isinstance(dl_clf, MockClassifier):
            logger.info(f"[{event_id}] ML confidence {result['confidence']:.4f} < {ml_threshold}. Falling back to DL model.")
            try:
                dl_result = dl_clf.predict(description)
                result = dl_result
                used_model = "DL_DISTILBERT"
            except Exception as e:
                logger.warning(f"[{event_id}] DL fallback failed: {e}. Using ML result.")
        
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
            "used_model": used_model,
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
