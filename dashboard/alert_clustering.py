"""
Alert Clustering Engine — Sentence Embeddings + HDBSCAN.

Hybrid pipeline:
  1. Known-variable substitution (device name from alert payload)
  2. Regex cascade (IPs, MACs, interfaces, percentages)
  3. Sentence embedding via all-MiniLM-L6-v2
  4. HDBSCAN clustering
  5. Template label extraction per cluster
"""

import re
import logging
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

import numpy as np

logger = logging.getLogger("AlertClustering")

# ---------------------------------------------------------------------------
# Regex patterns for variable token normalisation (applied in order)
# ---------------------------------------------------------------------------
_REGEX_CASCADE = [
    # IPv4 — must come before generic numbers
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "{IP}"),
    # MAC address
    (re.compile(r"\b(?:[0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}\b"), "{MAC}"),
    # UUID
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "{UUID}"),
    # Interface names (Cisco style)
    (re.compile(
        r"\b(?:GigabitEthernet|FastEthernet|TenGigE|TenGigabitEthernet|"
        r"FortyGigE|HundredGigE|Loopback|Vlan|Port-channel|Ethernet|"
        r"Management|Serial|Tunnel|BDI|AppGigabitEthernet)[0-9][0-9/:.]*\b", re.I
    ), "{IFACE}"),
    # Percentage values
    (re.compile(r"\b\d{1,3}(?:\.\d+)?\s*%"), "{PCT}"),
]

# Broad FQDN pattern — catches hostnames with 2+ dot-separated segments
_FQDN_PATTERN = re.compile(
    r"\b[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?){2,}\b"
)

# Standalone numbers (not part of a word) — applied last
_STANDALONE_NUM = re.compile(r"(?<![A-Za-z0-9_.])\b\d{2,}\b(?![A-Za-z0-9_.])")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class PatternCluster:
    cluster_id: int
    template: str
    alert_count: int
    devices: list = field(default_factory=list)
    category_breakdown: dict = field(default_factory=dict)
    suppression_rate: float = 0.0
    time_span: dict = field(default_factory=dict)
    hourly_distribution: list = field(default_factory=list)
    alerts: list = field(default_factory=list)
    noise: bool = False

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Clustering Engine
# ---------------------------------------------------------------------------
class AlertClusteringEngine:
    """Singleton-style engine. Loads sentence-transformers model once."""

    _instance: Optional["AlertClusteringEngine"] = None

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = None
        self._model_name = model_name

    @classmethod
    def get_instance(cls) -> "AlertClusteringEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading sentence-transformers model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
            logger.info("Sentence-transformers model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}")
            self._model = None

    # ---- Text normalisation ------------------------------------------------

    @staticmethod
    def normalize_text(text: str, device_name: str = None) -> str:
        """
        Replace known variables with typed placeholders.
        Step 1: Replace known device name (exact match).
        Step 2: Apply regex cascade for IPs, MACs, interfaces, etc.
        Step 3: Catch-all FQDN pattern.
        Step 4: Standalone numbers.
        """
        if not text:
            return ""

        normalized = text

        # Step 1 — known device name
        if device_name and device_name.strip():
            # Escape for regex safety, case-insensitive replacement
            pattern = re.compile(re.escape(device_name.strip()), re.IGNORECASE)
            normalized = pattern.sub("{DEVICE}", normalized)

        # Step 2 — regex cascade
        for pattern, placeholder in _REGEX_CASCADE:
            normalized = pattern.sub(placeholder, normalized)

        # Step 3 — remaining FQDNs
        normalized = _FQDN_PATTERN.sub("{FQDN}", normalized)

        # Step 4 — standalone numbers (conservative: only 2+ digit numbers)
        normalized = _STANDALONE_NUM.sub("{NUM}", normalized)

        # Collapse whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    # ---- Clustering --------------------------------------------------------

    def cluster(self, alerts: list) -> list:
        """
        Main entry point.
        Returns list of PatternCluster objects.
        """
        if not alerts:
            return []

        # Extract text + metadata from each alert
        texts = []
        device_names = []
        for a in alerts:
            details = a.get("alert_details") or {}
            text = (
                details.get("issue_details")
                or details.get("issue_name")
                or a.get("alert_details", {}).get("Assurance Issue Details", "")
                or ""
            )
            device = details.get("device_name") or details.get("device") or ""
            texts.append(str(text))
            device_names.append(str(device))

        # Normalise
        normalized = [
            self.normalize_text(t, d) for t, d in zip(texts, device_names)
        ]

        # Encode with sentence-transformers
        self._load_model()

        if self._model is not None:
            embeddings = self._model.encode(normalized, show_progress_bar=False)
            # L2-normalise for cosine-like HDBSCAN
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embeddings = embeddings / norms

            # HDBSCAN
            try:
                import hdbscan
                clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=2,
                    min_samples=1,
                    metric="euclidean",
                    cluster_selection_method="eom",
                )
                labels = clusterer.fit_predict(embeddings)
            except Exception as e:
                logger.error(f"HDBSCAN clustering failed: {e}")
                labels = self._fallback_clustering(normalized)
        else:
            # Fallback: group by exact normalized text hash
            labels = self._fallback_clustering(normalized)

        # Build clusters
        return self._build_clusters(labels, normalized, alerts)

    @staticmethod
    def _fallback_clustering(normalized_texts: list) -> np.ndarray:
        """Hash-based fallback when model is unavailable."""
        hash_to_id = {}
        labels = []
        next_id = 0
        for t in normalized_texts:
            h = hashlib.sha256(t.lower().encode()).hexdigest()
            if h not in hash_to_id:
                hash_to_id[h] = next_id
                next_id += 1
            labels.append(hash_to_id[h])
        return np.array(labels)

    def _build_clusters(
        self, labels: np.ndarray, normalized: list, alerts: list
    ) -> list:
        """Aggregate alerts into PatternCluster objects."""
        cluster_map = {}

        for idx, label in enumerate(labels):
            label_int = int(label)
            if label_int not in cluster_map:
                cluster_map[label_int] = {
                    "indices": [],
                    "normalized_texts": [],
                }
            cluster_map[label_int]["indices"].append(idx)
            cluster_map[label_int]["normalized_texts"].append(normalized[idx])

        results = []

        for label_int, data in sorted(cluster_map.items(), key=lambda x: -len(x[1]["indices"])):
            indices = data["indices"]
            cluster_alerts = [alerts[i] for i in indices]

            # Template = most common normalized text in the cluster
            from collections import Counter
            text_counts = Counter(data["normalized_texts"])
            template = text_counts.most_common(1)[0][0]

            # Compute stats
            devices = set()
            categories = {}
            timestamps = []
            backdated_count = 0
            auto_count = 0

            for a in cluster_alerts:
                details = a.get("alert_details") or {}
                results_data = a.get("results") or {}

                dev = details.get("device_name") or details.get("device") or "Unknown"
                devices.add(dev)

                is_bd = (results_data.get("agent_1", {}).get("data", {}).get("is_backdated", False))
                predicted = (results_data.get("agent_2", {}).get("data", {}).get("predicted_category", "") or "")

                if is_bd:
                    cat = "Backdated"
                    backdated_count += 1
                elif predicted.lower() == "auto resolving":
                    cat = "Auto Resolving"
                    auto_count += 1
                elif predicted.lower() == "non-auto resolving":
                    cat = "Non-Auto Resolving"
                else:
                    cat = "Uncertain"

                categories[cat] = categories.get(cat, 0) + 1

                ts = details.get("timestamp") or details.get("raw_timestamp")
                if ts:
                    timestamps.append(ts)

            # Time span
            parsed_ts = []
            for ts in timestamps:
                try:
                    if isinstance(ts, (int, float)):
                        dt = datetime.fromtimestamp(
                            ts / 1000 if ts > 1e12 else ts, tz=timezone.utc
                        )
                    else:
                        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                    parsed_ts.append(dt)
                except Exception:
                    pass

            time_span = {}
            if parsed_ts:
                parsed_ts.sort()
                time_span = {
                    "first": parsed_ts[0].isoformat(),
                    "last": parsed_ts[-1].isoformat(),
                }

            # Hourly distribution
            hourly = {}
            for dt in parsed_ts:
                hour_key = dt.strftime("%Y-%m-%d %H:00")
                hourly[hour_key] = hourly.get(hour_key, 0) + 1
            hourly_dist = [
                {"time": k, "count": v}
                for k, v in sorted(hourly.items())
            ]

            # Suppression rate
            total = len(cluster_alerts)
            suppressed = backdated_count + auto_count
            suppression_rate = round((suppressed / total * 100), 1) if total > 0 else 0

            # Strip alert sub-documents for response size (keep top-level fields only)
            slim_alerts = []
            for a in cluster_alerts:
                details = a.get("alert_details") or {}
                slim_alerts.append({
                    "event_id": details.get("event_id"),
                    "device_name": details.get("device_name") or details.get("device"),
                    "severity": details.get("severity"),
                    "issue_name": details.get("issue_name"),
                    "issue_details": details.get("issue_details"),
                    "timestamp": details.get("timestamp") or details.get("raw_timestamp"),
                    "category": categories,
                })

            results.append(PatternCluster(
                cluster_id=label_int,
                template=template,
                alert_count=total,
                devices=sorted(devices),
                category_breakdown=categories,
                suppression_rate=suppression_rate,
                time_span=time_span,
                hourly_distribution=hourly_dist,
                alerts=slim_alerts,
                noise=(label_int == -1),
            ))

        return results
