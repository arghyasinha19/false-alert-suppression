import os
import csv
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from workflow.classifier.model_ml import MLAlertClassifier
from workflow.classifier.preprocessor import clean_text, label_to_id, ID2LABEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_and_save(csv_path: str, model_out_path: str):
    logger.info(f"Loading data from {csv_path}...")
    
    texts = []
    labels = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            desc = row.get("description", "")
            cat = row.get("category", "")
            if desc and cat:
                # Clean text is normally handled in predict_batch, but we must do it for training
                texts.append(clean_text(desc))
                labels.append(label_to_id(cat))
                
    logger.info(f"Loaded {len(texts)} samples.")
    
    # Build pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000))
    ])
    
    logger.info("Training ML model...")
    pipeline.fit(texts, labels)
    
    # Evaluate on training data (just for sanity check)
    acc = pipeline.score(texts, labels)
    logger.info(f"Training accuracy: {acc:.4f}")
    
    classifier = MLAlertClassifier(pipeline=pipeline, label_mapping=ID2LABEL)
    classifier.save(model_out_path)
    logger.info("Training complete.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "alerts.csv")
    model_path = os.path.join(os.path.dirname(os.path.dirname(base_dir)), "models", "ml_model.joblib")
    
    train_and_save(csv_path, model_path)
