"""
DNAC Alert Classifier - Inference Model

Handles loading and running the fine-tuned DistilBERT model.
Uses ONNX Runtime for fast CPU inference by default, falling back to PyTorch
if ONNX is not available.
"""

import os
import json
import logging
from typing import Dict, List, Optional
import numpy as np
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

class AlertClassifier:
    """
    Wrapper for the trained alert classification model.
    """
    
    def __init__(
        self,
        tokenizer,
        onnx_session=None,
        pytorch_model=None,
        label_mapping: Optional[Dict[int, str]] = None,
        max_length: int = 128,
        model_metadata: Optional[Dict] = None,
    ):
        self.tokenizer = tokenizer
        self.onnx_session = onnx_session
        self.pytorch_model = pytorch_model
        
        # Use ONNX if available, else PyTorch
        self._backend = "onnx" if onnx_session is not None else "pytorch"
        
        self.max_length = max_length
        self.model_metadata = model_metadata or {}
        
        # Default label mapping if none provided
        if label_mapping:
            self.id2label = label_mapping
        else:
            self.id2label = {0: "Auto resolving", 1: "Non-Auto Resolving"}
            
    @classmethod
    def load(cls, model_dir: str):
        """
        Load the model from a directory.
        Supports three layouts:
          1. model.onnx at top level (ONNX Runtime)
          2. distilbert_model/ subdirectory (full training export)
          3. model.safetensors or pytorch_model.bin at top level (raw Trainer checkpoint)
        """
        onnx_path = os.path.join(model_dir, "model.onnx")
        pytorch_subdir = os.path.join(model_dir, "distilbert_model")
        metadata_path = os.path.join(model_dir, "evaluation_report.json")
        
        # Check if model_dir itself is a valid HuggingFace model directory
        has_safetensors = os.path.exists(os.path.join(model_dir, "model.safetensors"))
        has_pytorch_bin = os.path.exists(os.path.join(model_dir, "pytorch_model.bin"))
        has_config = os.path.exists(os.path.join(model_dir, "config.json"))
        is_hf_checkpoint = has_config and (has_safetensors or has_pytorch_bin)
        
        # Load metadata if it exists
        metadata = {}
        label_mapping = None
        max_length = 128
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    
                if "label_mapping" in metadata:
                    label_mapping = {int(k): v for k, v in metadata["label_mapping"].items()}
                
                if "max_length" in metadata:
                    max_length = metadata["max_length"]
                    
                logger.info(f"Loaded model metadata from {metadata_path}")
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
                
        onnx_session = None
        pytorch_model = None
        
        # Try ONNX first
        if os.path.exists(onnx_path):
            try:
                import onnxruntime as ort
                providers = ["CPUExecutionProvider"]
                onnx_session = ort.InferenceSession(onnx_path, providers=providers)
                logger.info(f"Loaded ONNX model from {onnx_path}")
            except ImportError:
                logger.warning(
                    "onnxruntime not installed. Install with: `pip install onnxruntime`.\n"
                    "Falling back to PyTorch."
                )
            except Exception as e:
                logger.warning(f"Failed to load ONNX model: {e}. Falling back to PyTorch.")

        # Fallback to PyTorch
        if onnx_session is None:
            # Determine where the PyTorch model lives
            if os.path.exists(pytorch_subdir):
                load_from = pytorch_subdir
            elif is_hf_checkpoint:
                load_from = model_dir
            else:
                raise FileNotFoundError(
                    f"No model found in {model_dir}.\n"
                    f"Expected model.onnx, distilbert_model/ directory, "
                    f"or model.safetensors/pytorch_model.bin + config.json.\n"
                    f"Run train_model.py first."
                )
            
            import torch
            from transformers import DistilBertForSequenceClassification
            
            pytorch_model = DistilBertForSequenceClassification.from_pretrained(load_from)
            pytorch_model.eval()

            device = "cuda" if torch.cuda.is_available() else "cpu"
            pytorch_model.to(device)

            logger.info(f"Loaded PyTorch model from {load_from} (device: {device})")
        
        # Load tokenizer
        # Priority: pytorch_subdir > model_dir > base pretrained model
        tokenizer = None
        for tokenizer_candidate in [pytorch_subdir, model_dir]:
            if os.path.exists(tokenizer_candidate):
                try:
                    tokenizer = AutoTokenizer.from_pretrained(tokenizer_candidate)
                    logger.info(f"Loaded tokenizer from {tokenizer_candidate}")
                    break
                except Exception:
                    continue
        
        if tokenizer is None:
            # Trainer checkpoints often don't save the tokenizer;
            # fall back to the base model tokenizer
            base_model_name = "distilbert-base-uncased"
            tokenizer = AutoTokenizer.from_pretrained(base_model_name)
            logger.info(f"Tokenizer not found in checkpoint, loaded base tokenizer: {base_model_name}")

        return cls(
            tokenizer=tokenizer,
            onnx_session=onnx_session,
            pytorch_model=pytorch_model,
            label_mapping=label_mapping,
            max_length=max_length,
            model_metadata=metadata,
        )

    # =========================================================================
    # Inference
    # =========================================================================

    def predict(self, description: str) -> Dict:
        """
        Classify a single alert description.
        
        Args:
            description: Raw alert description text.
        
        Returns:
            {
                "category": "Auto resolving" | "Non-Auto Resolving",
                "confidence": 0.0 - 1.0,
                "label_id": 0 | 1
            }
        """
        results = self.predict_batch([description])
        return results[0]

    def predict_batch(self, descriptions: List[str]) -> List[Dict]:
        """
        Classify a batch of alert descriptions.

        Args:
            descriptions: List of raw alert description texts.
        
        Returns:
            List of dicts, each with "category", "confidence", and "label_id".
        """
        from workflow.classifier.preprocessor import clean_text

        # Clean texts
        cleaned = [clean_text(d) for d in descriptions]

        # Tokenize
        encoded = self.tokenizer(
            cleaned,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="np" if self._backend == "onnx" else "pt",
        )

        # Run inference
        if self._backend == "onnx":
            logits = self._predict_onnx(encoded)
        else:
            logits = self._predict_pytorch(encoded)
        
        # Convert logits to predictions
        probabilities = self._softmax(logits)
        predicted_ids = np.argmax(probabilities, axis=-1)
        confidences = np.max(probabilities, axis=-1)

        results = []
        for pred_id, conf in zip(predicted_ids, confidences):
            results.append({
                "category": self.id2label.get(int(pred_id), f"Unknown({pred_id})"),
                "confidence": round(float(conf), 4),
                "label_id": int(pred_id)
            })
        
        return results

    def _predict_onnx(self, encoded) -> np.ndarray:
        """Run inference using ONNX Runtime."""
        ort_inputs = {
            "input_ids": encoded["input_ids"].astype(np.int64),
            "attention_mask": encoded["attention_mask"].astype(np.int64),
        }
        
        ort_outputs = self.onnx_session.run(None, ort_inputs)
        return ort_outputs[0]  # logits

    def _predict_pytorch(self, encoded) -> np.ndarray:
        """Run inference using PyTorch."""
        import torch

        device = next(self.pytorch_model.parameters()).device
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded["attention_mask"].to(device)

        with torch.no_grad():
            outputs = self.pytorch_model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
        return outputs.logits.cpu().numpy()

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        """Numerically stable softmax."""
        exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

    # =========================================================================
    # Model Info
    # =========================================================================

    def get_info(self) -> Dict:
        """Return metadata about the loaded model."""
        info = {
            "backend": self._backend,
            "max_length": self.max_length,
            "labels": self.id2label,
        }
        
        if self.model_metadata:
            info["model_name"] = self.model_metadata.get("model_name", "unknown")
            info["training_time_seconds"] = self.model_metadata.get("training_time_seconds")
            info["training_samples"] = self.model_metadata.get("training_samples")
            info["device_trained_on"] = self.model_metadata.get("device")
            
            test_metrics = self.model_metadata.get("test_metrics", {})
            if test_metrics:
                info["test_accuracy"] = test_metrics.get("accuracy")
                info["test_f1"] = test_metrics.get("f1")
                info["test_precision"] = test_metrics.get("precision")
                info["test_recall"] = test_metrics.get("recall")
                
        return info
