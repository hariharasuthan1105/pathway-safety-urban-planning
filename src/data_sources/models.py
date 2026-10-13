"""
Unified CityEvent Schema and Normalization Model for Phase 3.
Provides standardized formatting for both real external API feeds and simulated telemetry streams.
"""

import uuid
import math
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
    
    if latitude is not None and (not math.isfinite(float(latitude)) or not -90 <= float(latitude) <= 90):
        raise ValueError("Latitude must be finite and between -90 and 90")
    if longitude is not None and (not math.isfinite(float(longitude)) or not -180 <= float(longitude) <= 180):
        raise ValueError("Longitude must be finite and between -180 and 180")
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
            "lat": float(latitude) if latitude is not None else None,
            "lon": float(longitude) if longitude is not None else None,
            "zone": zone
        }
    }
