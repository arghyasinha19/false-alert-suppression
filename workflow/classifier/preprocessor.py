"""
Text Preprocessing for DNAC Alert Descriptions

Deterministic, stateless cleaning functions used during both
training and inference to ensure consistency.
"""

import re
import html
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# =========================================================================
# Label Mapping
# =========================================================================

# Canonical label names -> integer IDs
LABEL2ID: Dict[str, int] = {
    "Auto resolving": 0,
    "Non-Auto Resolving": 1,
}

ID2LABEL: Dict[int, str] = {v: k for k, v in LABEL2ID.items()}

# Common typo / casing variants that appear in real datasets
_LABEL_ALIASES: Dict[str, str] = {
    "auto resolving": "Auto resolving",
    "auto-resolving": "Auto resolving",
    "autoresolving": "Auto resolving",
    "auto resolve": "Auto resolving",
    "non-auto resolving": "Non-Auto Resolving",
    "non auto resolving": "Non-Auto Resolving",
    "non-auto resolveing": "Non-Auto Resolving", # known typo in dataset
    "nonautoresolving": "Non-Auto Resolving",
    "non-auto-resolving": "Non-Auto Resolving",
    "non-auto resolve": "Non-Auto Resolving",
}

# =========================================================================
# Text Cleaning
# =========================================================================

def clean_text(text: str) -> str:
    """
    Clean and normalize an alert description for model input.

    Steps:
    1. Unescape HTML entities
    2. Remove HTML tags
    3. Mask IPs, MACs, Hostnames, and Numbers
    4. Collapse whitespace (newlines, tabs, multiple spaces)
    5. Strip leading/trailing whitespace
    6. Lowercase
    """
    if not isinstance(text, str):
        return ""

    # Unescape HTML entities (e.g., &amp; -> &)
    text = html.unescape(text)

    # Remove any HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Mask IP Addresses
    text = re.sub(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "[IP]", text)
    
    # Mask MAC Addresses
    text = re.sub(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b", "[MAC]", text)

    # Mask specific known hostnames / domains (anything ending in .corp, .com, etc.)
    text = re.sub(r"\b[A-Za-z0-9\-]+\.[A-Za-z0-9\-\.]+\.corp\b", "[HOSTNAME]", text)
    text = re.sub(r"\b[A-Za-z0-9\-]+\.[A-Za-z0-9\-\.]+\.com\b", "[HOSTNAME]", text)
    # Also mask device names that look like switch/router names e.g. at-vie-core01
    text = re.sub(r"\b[a-z]{2,3}-[a-z]{2,3}-[a-z0-9\-]+\b", "[DEVICE]", text, flags=re.IGNORECASE)

    # Replace common separator patterns with spaces
    text = re.sub(r"[_|]+", " ", text)

    # Mask Numbers
    text = re.sub(r"\b\d+\b", "[NUM]", text)

    # Collapse all whitespace (tabs, newlines, multiple spaces) into single space
    text = re.sub(r"\s+", " ", text)

    # Strip and lowercase
    text = text.strip().lower()

    return text

# =========================================================================
# Label Normalization
# =========================================================================

def normalize_label(label: str) -> str:
    """
    Map a raw label string to its canonical form.

    Handles casing differences, typos (e.g., 'Resolveing'), and common
    formatting variations. Raises ValueError for unrecognized labels.
    """
    if not isinstance(label, str):
        raise ValueError(f"Label must be a string, got {type(label)}: {label}")

    normalized = label.strip()
    lookup_key = normalized.lower()

    # Direct match on canonical name (case-insensitive)
    for canonical in LABEL2ID:
        if canonical.lower() == lookup_key:
            return canonical

    # Check aliases
    if lookup_key in _LABEL_ALIASES:
        return _LABEL_ALIASES[lookup_key]

    raise ValueError(
        f"Unrecognized label: '{label}'. "
        f"Expected one of: {list(LABEL2ID.keys())} or known aliases."
    )

def label_to_id(label: str) -> int:
    """Convert a (possibly messy) label string to its integer ID."""
    return LABEL2ID[normalize_label(label)]

def id_to_label(label_id: int) -> str:
    """Convert an integer ID back to the canonical label string."""
    if label_id not in ID2LABEL:
        raise ValueError(f"Unknown label ID: {label_id}. Expected one of: {list(ID2LABEL.keys())}")
    return ID2LABEL[label_id]
