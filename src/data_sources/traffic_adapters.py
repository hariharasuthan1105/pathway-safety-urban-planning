"""
Honest Traffic Connectors and Adapter Interface (§4).

Explicitly distinguishes real external traffic providers (TomTom, Google Maps)
from local traffic simulation. Does not fabricate traffic observations when
credentials or endpoints are unconfigured.

Required Environment Variables & Provider Specifications:
1. TomTom Traffic Flow & Incidents:
   - Credential: TOMTOM_API_KEY (Commercial / Freemium API key)
   - Flow Endpoint: https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json?point={lat},{lon}&key={key}
   - Incidents Endpoint: https://api.tomtom.com/traffic/services/5/incidentDetails?bbox={min_lon},{min_lat},{max_lon},{max_lat}&key={key}
   - Expected Response Schema:
     {
       "flowSegmentData": {
         "currentSpeed": float (km/h),
         "freeFlowSpeed": float (km/h),
         "currentTravelTime": int (seconds),
         "freeFlowTravelTime": int (seconds),
         "confidence": float (0.0 - 1.0)
       }
     }

2. Google Maps Routes / Traffic:
   - Credential: GOOGLE_MAPS_TRAFFIC_API_KEY (GCP Project with Routes API enabled)
   - Endpoint: https://routes.googleapis.com/directions/v2:computeRoutes
   - Headers: X-Goog-Api-Key: {key}, X-Goog-FieldMask: routes.duration,routes.staticDuration
   - Body: {"origin": {...}, "destination": {...}, "routingPreference": "TRAFFIC_AWARE_OPTIMAL"}
   - Expected Response Schema:
     {
       "routes": [
         {
           "duration": string (e.g. "1240s"),
           "staticDuration": string (e.g. "900s")
         }
       ]
     }
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class BaseTrafficConnector(ABC):
    """Smallest compatible traffic provider adapter interface."""
    provider_name: str = "base"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True only when valid provider credentials and endpoints are present."""
        pass

    @abstractmethod
    def fetch_flow(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Fetches live segment flow observations. Returns None if provider is unconfigured or request fails.
        Never fabricates fallback measurements.
        """
        pass


class TomTomTrafficConnector(BaseTrafficConnector):
    provider_name = "tomtom"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = os.getenv("TOMTOM_API_KEY", "").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.lower() != "your_tomtom_api_key")

    def fetch_flow(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        if not self.is_configured():
            logger.debug("[TomTom Traffic] Connector is unconfigured (TOMTOM_API_KEY missing).")
            return None
        # Actual HTTP fetch would execute here once user supplies approved key
        return None


class GoogleTrafficConnector(BaseTrafficConnector):
    provider_name = "google"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = os.getenv("GOOGLE_MAPS_TRAFFIC_API_KEY", "").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.lower() != "your_google_api_key")

    def fetch_flow(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        if not self.is_configured():
            logger.debug("[Google Traffic] Connector is unconfigured (GOOGLE_MAPS_TRAFFIC_API_KEY missing).")
            return None
        return None
