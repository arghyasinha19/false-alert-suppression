from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

# -------------------------------------------------------------------------
# Result model (easy to test)
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class BackdateDecision:
    is_backdated: bool
    reason: str
    event_timestamp_ms: Optional[int]
    ingestion_timestamp_ms: int
    skew_ms: Optional[int]
    threshold_ms: int
    
    # NEW: Human-readable explanation
    explanation: str
    
    # helpful metadata for downstream/logging (keys unchanged)
    instance_id: Optional[str] = None
    event_id: Optional[str] = None
    correlation_id: Optional[str] = None
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    
# -------------------------------------------------------------------------
# Detector
# -------------------------------------------------------------------------
class BackdateDetector:
    """
    Detects back-dated DNAC alerts based on:
      skew_ms = ingestion_time_ms - event_time_ms
      
    If skew_ms > threshold_ms => backdated (false upfront)
    """
    
    def __init__(
        self,
        threshold_minutes: int = 5,
        allow_future_skew_seconds: int = 60,
        max_reasonable_age_days: int = 30,
        logger: Optional[logging.Logger] = None,
    ):
        if threshold_minutes <= 0:
            raise ValueError("threshold_minutes must be > 0")
            
        self.threshold_minutes = threshold_minutes
        self.threshold_ms = threshold_minutes * 60 * 1000
        self.allow_future_skew_ms = allow_future_skew_seconds * 1000
        self.max_reasonable_age_ms = max_reasonable_age_days * 24 * 60 * 60 * 1000
        
        self.log = logger or logging.getLogger("dnac.backdate")
        
    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def evaluate(
        self,
        payload: Dict[str, Any],
        ingestion_time: Optional[datetime] = None,
    ) -> BackdateDecision:
        ingestion_ms = self._get_ingestion_ms(ingestion_time)
        event_ms = self._extract_event_timestamp_ms(payload)
        meta = self._extract_metadata(payload)
        
        # Missing timestamp -> fail closed
        if event_ms is None:
            explanation = (
                f"Event timestamp is missing/invalid; cannot compute alert age. "
                f"Permissible threshold is {self.threshold_minutes} mins. "
                f"Policy: flag as backdated upfront."
            )
            decision = BackdateDecision(
                is_backdated=True,
                reason="MISSING_EVENT_TIMESTAMP",
                event_timestamp_ms=None,
                ingestion_timestamp_ms=ingestion_ms,
                skew_ms=None,
                threshold_ms=self.threshold_ms,
                explanation=explanation,
                **meta,
            )
            self._log_decision(decision, level="warning")
            return decision
            
        skew_ms = ingestion_ms - event_ms
        
        # Event in future beyond allowed skew -> invalid/suspicious
        if skew_ms < -self.allow_future_skew_ms:
            explanation = (
                f"Alert timestamp appears in the future beyond allowed skew. "
                f"Event time: {self._ms_to_iso(event_ms)}; Ingestion time: {self._ms_to_iso(ingestion_ms)}. "
                f"Future skew: {self._format_duration(skew_ms)}. "
                f"Allowed future skew is {self.allow_future_skew_ms // 1000} seconds. "
                f"Policy: flag as backdated/suspicious upfront."
            )
            decision = BackdateDecision(
                is_backdated=True,
                reason="EVENT_TIMESTAMP_IN_FUTURE_BEYOND_ALLOWED_SKEW",
                event_timestamp_ms=event_ms,
                ingestion_timestamp_ms=ingestion_ms,
                skew_ms=skew_ms,
                threshold_ms=self.threshold_ms,
                explanation=explanation,
                **meta,
            )
            self._log_decision(decision, level="warning")
            return decision
            
        # Absurdly old -> sanity limit
        if skew_ms > self.max_reasonable_age_ms:
            explanation = (
                f"Actual alert date is {self._format_duration(skew_ms)} ago "
                f"(event={self._ms_to_iso(event_ms)}, ingestion={self._ms_to_iso(ingestion_ms)}) "
                f"which exceeds sanity limit of {self.max_reasonable_age_ms // (24 * 60 * 60 * 1000)} days. "
                f"Permissible threshold is {self.threshold_minutes} mins. "
                f"Policy: flag as backdated/invalid upfront."
            )
            decision = BackdateDecision(
                is_backdated=True,
                reason="EVENT_TIMESTAMP_TOO_OLD_SANITY_LIMIT",
                event_timestamp_ms=event_ms,
                ingestion_timestamp_ms=ingestion_ms,
                skew_ms=skew_ms,
                threshold_ms=self.threshold_ms,
                explanation=explanation,
                **meta,
            )
            self._log_decision(decision, level="warning")
            return decision
            
        # Core rule: threshold in minutes
        if skew_ms > self.threshold_ms:
            # ✅ This line matches your ask exactly
            explanation = (
                f"Actual alert date is {self._format_duration(skew_ms)} ago "
                f"where the permissible threshold is {self.threshold_minutes} mins."
            )
            decision = BackdateDecision(
                is_backdated=True,
                reason="BACKDATED_THRESHOLD_EXCEEDED",
                event_timestamp_ms=event_ms,
                ingestion_timestamp_ms=ingestion_ms,
                skew_ms=skew_ms,
                threshold_ms=self.threshold_ms,
                explanation=explanation,
                **meta,
            )
            self._log_decision(decision, level="warning")
            return decision
            
        # Fresh
        explanation = (
            f"Alert is within permissible threshold. "
            f"Observed delay is {self._format_duration(skew_ms)}; "
            f"threshold is {self.threshold_minutes} mins."
        )
        decision = BackdateDecision(
            is_backdated=False,
            reason="FRESH_WITHIN_THRESHOLD",
            event_timestamp_ms=event_ms,
            ingestion_timestamp_ms=ingestion_ms,
            skew_ms=skew_ms,
            threshold_ms=self.threshold_ms,
            explanation=explanation,
            **meta,
        )
        self._log_decision(decision, level="debug")
        return decision
        
    # -------------------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------------------
    def _get_ingestion_ms(self, ingestion_time: Optional[datetime]) -> int:
        dt = ingestion_time or datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
        
    def _extract_event_timestamp_ms(self, payload: Dict[str, Any]) -> Optional[int]:
        """
        Uses your payload key: 'raw_timestamp'
        Supports:
          - int/float (ms or seconds)
          - numeric string
          - ISO 8601 string
        """
        raw = payload.get("raw_timestamp")
        
        if raw is None:
            return None
            
        if isinstance(raw, (int, float)):
            return self._normalize_epoch_to_ms(raw)
            
        if isinstance(raw, str):
            s = raw.strip()
            if s.isdigit():
                return self._normalize_epoch_to_ms(int(s))
                
            iso_ms = self._try_parse_iso_to_ms(s)
            if iso_ms is not None:
                return iso_ms
                
        return None

    def _normalize_epoch_to_ms(self, value: Union[int, float]) -> int:
        """
        Heuristic:
          - >= 1e12 => ms
          - else => seconds
        """
        if value >= 1_000_000_000_000:
            return int(value)
        return int(value * 1000)
        
    def _try_parse_iso_to_ms(self, value: str) -> Optional[int]:
        try:
            v = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except Exception:
            return None
            
    def _extract_metadata(self, payload: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Uses your payload keys exactly:
          - instance_id, event_id, correlation_id
          - network.device_id
          - details.device_name
        """
        details = payload.get("details") or {}
        network = payload.get("network") or {}
        
        return {
            "instance_id": payload.get("instanceId"),
            "event_id": payload.get("eventId"),
            "correlation_id": payload.get("correlationId"),
            "device_id": network.get("deviceId"),
            "device_name": details.get("deviceName"),
        }
        
    def _format_duration(self, ms: int) -> str:
        """
        Converts milliseconds to a human readable duration like:
        '10 days 4 hrs 9 mins 28 secs'
        """
        if ms is None:
            return "N/A"
            
        negative = ms < 0
        ms = abs(ms)
        
        seconds = ms // 1000
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        
        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hr{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
        parts.append(f"{secs} sec{'s' if secs != 1 else ''}")
        
        text = " ".join(parts)
        return f"-{text}" if negative else text
        
    def _ms_to_iso(self, ms: int) -> str:
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        return dt.isoformat()
        
    def _log_decision(self, decision: BackdateDecision, level: str = "info") -> None:
        msg = {
            "component": "dnac_backdate_detector",
            "is_backdated": decision.is_backdated,
            "reason": decision.reason,
            "event_timestamp_ms": decision.event_timestamp_ms,
            "ingestion_timestamp_ms": decision.ingestion_timestamp_ms,
            "skew_ms": decision.skew_ms,
            "threshold_ms": decision.threshold_ms,
            
            # ✅ NEW: explanation included in output
            "explanation": decision.explanation,
            
            "instanceId": decision.instance_id,
            "eventId": decision.event_id,
            "correlationId": decision.correlation_id,
            "deviceId": decision.device_id,
            "deviceName": decision.device_name,
        }
        
        line = json.dumps(msg, separators=(",", ":"), ensure_ascii=False)
        log_fn = getattr(self.log, level, self.log.info)
        log_fn(line)
