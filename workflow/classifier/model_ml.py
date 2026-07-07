import os
import joblib
import logging
from typing import Dict, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from workflow.classifier.preprocessor import clean_text

logger = logging.getLogger(__name__)

class MLAlertClassifier:
    """
    TF-IDF + LogisticRegression model for alert classification.
    Provides a compatible API with AlertClassifier.
    """
    def __init__(self, pipeline: Pipeline = None, label_mapping: Optional[Dict[int, str]] = None):
        self.pipeline = pipeline
        self.id2label = label_mapping or {0: "Auto resolving", 1: "Non-Auto Resolving"}

    @classmethod
    def load(cls, model_path: str):
        """Load the ML model from a joblib file."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        
        try:
            data = joblib.load(model_path)
            pipeline = data.get("pipeline")
            label_mapping = data.get("label_mapping")
            logger.info(f"Loaded ML model from {model_path}")
            return cls(pipeline=pipeline, label_mapping=label_mapping)
        except Exception as e:
            logger.error(f"Failed to load ML model from {model_path}: {e}")
            raise

    def save(self, model_path: str):
        """Save the ML model to a joblib file."""
        os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
        data = {
            "pipeline": self.pipeline,
            "label_mapping": self.id2label
        }
        joblib.dump(data, model_path)
        logger.info(f"Saved ML model to {model_path}")

    def predict(self, description: str) -> Dict:
        """Classify a single alert description."""
        results = self.predict_batch([description])
        return results[0]

    def predict_batch(self, descriptions: List[str]) -> List[Dict]:
        """Classify a batch of alert descriptions."""
        if self.pipeline is None:
            raise ValueError("Model pipeline is not initialized or loaded.")
            
        cleaned = [clean_text(d) for d in descriptions]
        
        # predict_proba returns array of shape (n_samples, n_classes)
        probabilities = self.pipeline.predict_proba(cleaned)
        predicted_ids = np.argmax(probabilities, axis=1)
        confidences = np.max(probabilities, axis=1)

        results = []
        for pred_id, conf in zip(predicted_ids, confidences):
            results.append({
                "category": self.id2label.get(int(pred_id), f"Unknown({pred_id})"),
                "confidence": round(float(conf), 4),
                "label_id": int(pred_id)
            })
        
        return results
