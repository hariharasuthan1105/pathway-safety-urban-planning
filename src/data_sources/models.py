"""
Unified CityEvent Schema and Normalization Model for Phase 3.
Provides standardized formatting for both real external API feeds and simulated telemetry streams.
"""

import uuid
import datetime
from typing import Dict, Any, Optional

def create_city_event(
    source: str,
    event_type: str,
    latitude: float,
    longitude: float,
    data: Dict[str, Any],
    severity: str = "LOW",
    zone: str = "city_center",
    event_id: Optional[str] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs a normalized CityEvent dictionary matching Pathway streaming schema.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Ensure inner payload includes key metadata for UI & Anomaly UDF processing
    payload = dict(data)
    payload["event_id"] = event_id or f"{source}_{uuid.uuid4().hex[:8]}"
    payload["event_type"] = event_type
    payload["severity"] = severity
    
    return {
        "timestamp": timestamp or now_iso,
        "source": source,
        "data": payload,
        "location": {
            "lat": round(float(latitude), 4),
            "lon": round(float(longitude), 4),
            "zone": zone
        }
    }
