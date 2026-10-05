"""
Streaming Rolling Time Window Aggregator for Phase 4.
Maintains sliding windows (5m, 15m, 30m, 60m) to measure event rates,
severity frequency, and rate-of-change acceleration.
"""

import datetime
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RollingWindowAggregator:
    def __init__(self, max_history_minutes: int = 60):
        self.max_history_minutes = max_history_minutes
        self.events_history: List[Dict[str, Any]] = []

    def add_event(self, event: Dict[str, Any]):
        """
        Ingests a new normalized CityEvent and purges expired history.
        """
        if isinstance(event, dict):
            self.events_history.append(event)
            self._purge_expired()

    def _purge_expired(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(minutes=self.max_history_minutes)
        
        valid_events = []
        for ev in self.events_history:
            ts_str = ev.get("timestamp")
            try:
                dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if dt >= cutoff:
                    valid_events.append(ev)
            except Exception:
                valid_events.append(ev)
        self.events_history = valid_events

    def get_events_in_window(self, minutes: int) -> List[Dict[str, Any]]:
        """
        Returns all events arriving within the last N minutes.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(minutes=minutes)
        results = []
        for ev in self.events_history:
            ts_str = ev.get("timestamp")
            try:
                dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if dt >= cutoff:
                    results.append(ev)
            except Exception:
                results.append(ev)
        return results

    def compute_metrics(self) -> Dict[str, Any]:
        """
        Computes window statistics across 5m, 15m, 30m, and 60m.
        """
        self._purge_expired()
        
        w5 = self.get_events_in_window(5)
        w15 = self.get_events_in_window(15)
        w30 = self.get_events_in_window(30)
        w60 = self.get_events_in_window(60)

        # Rate of change / acceleration calculation
        rate_5m = len(w5)
        rate_15m = len(w15)
        expected_5m = rate_15m / 3.0 if rate_15m > 0 else 0.0
        acceleration = (rate_5m / expected_5m) if expected_5m > 0 else 1.0

        return {
            "count_5m": len(w5),
            "count_15m": len(w15),
            "count_30m": len(w30),
            "count_60m": len(w60),
            "acceleration_ratio": round(acceleration, 2),
            "events_5m": w5,
            "events_15m": w15
        }
