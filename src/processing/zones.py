"""
Geographic Zone Intelligence & Spatial Bucketing for Phase 4.
Maps latitude/longitude coordinates to deterministic geographic zones
and computes per-zone risk, event density, and activity trends.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Configurable Default Zone Boundaries (e.g. NYC / Standard Metropolitan Area)
DEFAULT_ZONES = [
    {"name": "Zone A (Downtown)", "lat_min": 40.70, "lat_max": 40.73, "lon_min": -74.02, "lon_max": -73.98},
    {"name": "Zone B (Midtown)", "lat_min": 40.73, "lat_max": 40.76, "lon_min": -74.01, "lon_max": -73.96},
    {"name": "Zone C (Uptown)", "lat_min": 40.76, "lat_max": 40.80, "lon_min": -73.98, "lon_max": -73.93},
    {"name": "Zone D (Outer District)", "lat_min": -90.0, "lat_max": 90.0, "lon_min": -180.0, "lon_max": 180.0}
]

def get_zone_name(lat: float, lon: float, zones_config: List[Dict[str, Any]] = None) -> str:
    """
    Determines zone name for given latitude and longitude coordinates.
    """
    zones = zones_config or DEFAULT_ZONES
    for z in zones:
        if z["lat_min"] <= lat <= z["lat_max"] and z["lon_min"] <= lon <= z["lon_max"]:
            return z["name"]
    return "Zone D (Outer District)"

class ZoneManager:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.zones_config = self.config.get("zones", DEFAULT_ZONES)

    def assign_zone(self, event: Dict[str, Any]) -> str:
        if "location" not in event or not isinstance(event.get("location"), dict):
            event["location"] = {"lat": 40.7128, "lon": -74.0060}
        
        location = event["location"]
        lat = location.get("lat", 40.7128)
        lon = location.get("lon", -74.0060)
        
        # If zone already set explicitly, preserve it
        if "zone" in location and location["zone"] and location["zone"] != "city_center":
            return location["zone"]
        
        zone_name = get_zone_name(lat, lon, self.zones_config)
        location["zone"] = zone_name
        return zone_name

    def summarize_zones(self, events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Summarizes event density, anomaly counts, and risk scores per zone.
        """
        zone_summary: Dict[str, Dict[str, Any]] = {}

        for z in DEFAULT_ZONES:
            name = z["name"]
            zone_summary[name] = {
                "name": name,
                "event_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "anomaly_count": 0,
                "sources": set(),
                "risk_score": 0,
                "risk_level": "LOW"
            }

        for ev in events:
            loc = ev.get("location", {})
            zone_name = loc.get("zone") if isinstance(loc, dict) else "Zone A (Downtown)"
            if zone_name not in zone_summary:
                zone_summary[zone_name] = {
                    "name": zone_name,
                    "event_count": 0,
                    "critical_count": 0,
                    "high_count": 0,
                    "anomaly_count": 0,
                    "sources": set(),
                    "risk_score": 0,
                    "risk_level": "LOW"
                }

            z = zone_summary[zone_name]
            z["event_count"] += 1
            z["sources"].add(ev.get("source", "unknown"))

            data = ev.get("data", {}) if isinstance(ev.get("data"), dict) else {}
            sev = data.get("severity", ev.get("severity", "LOW")).upper()

            if sev == "CRITICAL":
                z["critical_count"] += 1
            elif sev == "HIGH":
                z["high_count"] += 1

            if data.get("anomaly", False):
                z["anomaly_count"] += 1

        # Calculate per-zone risk scores
        for z in zone_summary.values():
            z["sources"] = list(z["sources"])
            score = (z["critical_count"] * 30) + (z["high_count"] * 18) + (z["anomaly_count"] * 15) + (z["event_count"] * 3)
            # Multi-source bonus
            if len(z["sources"]) >= 2:
                score = int(score * 1.2)

            z["risk_score"] = min(100, score)
            z["risk_level"] = "CRITICAL" if z["risk_score"] > 75 else ("HIGH" if z["risk_score"] > 50 else ("MODERATE" if z["risk_score"] > 25 else "LOW"))

        return zone_summary
