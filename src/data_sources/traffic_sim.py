"""
Realistic Backend Traffic Simulation Source for South India Urban Intelligence (§6).

Features:
- Operates backend-side only, streaming events into Pathway via pw.io.python.read.
- Seedable (TRAFFIC_SIM_SEED) for deterministic testing.
- Per-city profile across 20 South Indian cities (baseline demand, road segments, IST peak curves, weather coupling).
- Emits CityEvent with source='traffic_simulation' and mode='SIMULATED'.
"""

import time
import datetime
import random
import logging
from typing import Dict, Any, List, Optional

from .base import DataSource
from .real_sources import SOUTH_INDIA_CITIES, EventSchema
from .models import create_city_event

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

logger = logging.getLogger(__name__)

# Road segment metadata per city for realistic spatial mapping
CITY_ROAD_NETWORKS: Dict[str, List[Dict[str, Any]]] = {
    "Chennai": [
        {"segment": "Anna Salai (Mount Road)", "offset_lat": 0.01, "offset_lon": -0.01, "capacity": 2500},
        {"segment": "GST Road (Airport Corridor)", "offset_lat": -0.03, "offset_lon": -0.02, "capacity": 3000},
        {"segment": "OMR (IT Expressway)", "offset_lat": -0.05, "offset_lon": 0.03, "capacity": 2800},
        {"segment": "ECR (East Coast Road)", "offset_lat": -0.04, "offset_lon": 0.04, "capacity": 1800},
    ],
    "Coimbatore": [
        {"segment": "Avinashi Road Corridor", "offset_lat": 0.01, "offset_lon": 0.02, "capacity": 1800},
        {"segment": "Trichy Road Bypass", "offset_lat": -0.01, "offset_lon": 0.01, "capacity": 1600},
    ],
    "Madurai": [
        {"segment": "Meenakshi Temple Outer Ring", "offset_lat": 0.005, "offset_lon": 0.005, "capacity": 1400},
        {"segment": "TPK Road South", "offset_lat": -0.01, "offset_lon": -0.01, "capacity": 1500},
    ],
    "Salem": [
        {"segment": "Five Roads Junction Corridor", "offset_lat": 0.01, "offset_lon": 0.005, "capacity": 1500},
    ],
    "Tiruchirappalli": [
        {"segment": "Thillai Nagar Main Road", "offset_lat": 0.008, "offset_lon": -0.005, "capacity": 1400},
    ],
    "Tiruppur": [
        {"segment": "Avinashi Road Industrial Belt", "offset_lat": 0.01, "offset_lon": 0.01, "capacity": 1300},
    ],
    "Erode": [
        {"segment": "Bhavani Road Transit Corridor", "offset_lat": 0.005, "offset_lon": 0.008, "capacity": 1200},
    ],
    "Vellore": [
        {"segment": "Fort Outer Ring Corridor", "offset_lat": 0.005, "offset_lon": -0.005, "capacity": 1200},
    ],
    "Kochi": [
        {"segment": "MG Road Ernakulam", "offset_lat": 0.005, "offset_lon": -0.005, "capacity": 2000},
        {"segment": "Vyttila Mobility Hub Junction", "offset_lat": -0.02, "offset_lon": 0.02, "capacity": 2400},
        {"segment": "Kalamassery Highway Arc", "offset_lat": 0.04, "offset_lon": 0.02, "capacity": 2200},
    ],
    "Thiruvananthapuram": [
        {"segment": "MG Road Statue Corridor", "offset_lat": 0.005, "offset_lon": -0.005, "capacity": 1800},
        {"segment": "Kazhakkoottam Technopark Highway", "offset_lat": 0.05, "offset_lon": -0.02, "capacity": 2500},
    ],
    "Kozhikode": [
        {"segment": "Mavoor Road Commercial Corridor", "offset_lat": 0.008, "offset_lon": 0.005, "capacity": 1500},
    ],
    "Thrissur": [
        {"segment": "Swaraj Round Ring", "offset_lat": 0.003, "offset_lon": 0.003, "capacity": 1600},
    ],
    "Kollam": [
        {"segment": "Chinnakada Clock Tower Junction", "offset_lat": 0.005, "offset_lon": -0.005, "capacity": 1300},
    ],
    "Kannur": [
        {"segment": "Calicut Road South Arc", "offset_lat": -0.008, "offset_lon": 0.005, "capacity": 1200},
    ],
    "Visakhapatnam": [
        {"segment": "Beach Road Promenade", "offset_lat": 0.01, "offset_lon": 0.02, "capacity": 1800},
        {"segment": "Dwaraka Nagar Commercial Hub", "offset_lat": 0.005, "offset_lon": -0.01, "capacity": 2200},
        {"segment": "Gajuwaka Industrial Highway", "offset_lat": -0.04, "offset_lon": -0.03, "capacity": 2600},
    ],
    "Vijayawada": [
        {"segment": "Bandar Road Corridor", "offset_lat": 0.01, "offset_lon": 0.015, "capacity": 2000},
        {"segment": "Benz Circle Transit Hub", "offset_lat": 0.005, "offset_lon": 0.01, "capacity": 2400},
    ],
    "Guntur": [
        {"segment": "Nizamapatnam Road Junction", "offset_lat": 0.005, "offset_lon": 0.008, "capacity": 1400},
    ],
    "Tirupati": [
        {"segment": "Alipiri Footpath Approach Road", "offset_lat": 0.015, "offset_lon": -0.01, "capacity": 1600},
    ],
    "Nellore": [
        {"segment": "GNT Road Highway Segment", "offset_lat": 0.008, "offset_lon": 0.005, "capacity": 1400},
    ],
    "Kurnool": [
        {"segment": "Bellary Road Corridor", "offset_lat": 0.005, "offset_lon": -0.008, "capacity": 1300},
    ]
}

class TrafficSimulationSource(DataSource):
    name = "traffic_simulation"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cities = SOUTH_INDIA_CITIES
        self.interval = self.config.get('data_sources', {}).get('traffic', {}).get('poll_interval', 5)
        self.status = "SIMULATED"
        self.last_updated = "N/A"

        # Seed setup for deterministic tests if specified
        seed_val = self.config.get('traffic_sim_seed')
        self.rng = random.Random(seed_val) if seed_val is not None else random.Random()

        # Internal state tracking per city road segment for smooth realistic transitions
        self.segment_state: Dict[str, Dict[str, Any]] = {}
        self._init_segment_states()

    def _init_segment_states(self):
        for c in self.cities:
            city_name = c["city"]
            segments = CITY_ROAD_NETWORKS.get(city_name, [
                {"segment": f"{city_name} Central Corridor", "offset_lat": 0.0, "offset_lon": 0.0, "capacity": 1500}
            ])
            for seg in segments:
                key = f"{city_name}::{seg['segment']}"
                self.segment_state[key] = {
                    "city": city_name,
                    "state": c["state"],
                    "base_lat": c["lat"],
                    "base_lon": c["lon"],
                    "segment": seg["segment"],
                    "offset_lat": seg["offset_lat"],
                    "offset_lon": seg["offset_lon"],
                    "capacity": seg["capacity"],
                    "congestion_level": self.rng.uniform(0.15, 0.45),
                    "avg_speed_kmh": self.rng.uniform(30.0, 45.0),
                    "active_incident": False,
                    "incident_duration_ticks": 0
                }

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)

    def _calculate_ist_peak_factor(self) -> float:
        """Calculates IST time-of-day traffic demand multiplier (AM & PM peak hour curves)."""
        # IST is UTC+5:30
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        ist_hour = (now_utc.hour + 5 + (now_utc.minute + 30) // 60) % 24

        # Morning Peak: 8:00 AM - 10:30 AM
        if 8 <= ist_hour <= 10:
            return 1.65
        # Evening Peak: 5:00 PM - 8:30 PM
        elif 17 <= ist_hour <= 20:
            return 1.85
        # Mid-day
        elif 11 <= ist_hour <= 16:
            return 1.20
        # Late Night: 11:00 PM - 5:00 AM
        elif ist_hour >= 23 or ist_hour <= 5:
            return 0.35
        else:
            return 1.0

    def _stream(self):
        from ..processing.shared_state import get_shared_city_state_manager

        while True:
            peak_factor = self._calculate_ist_peak_factor()
            
            # Fetch current weather state from CityStateManager if available for weather coupling
            weather_coupling_factor = 1.0
            city_state_mgr = None
            try:
                city_state_mgr = get_shared_city_state_manager()
            except Exception:
                pass

            for key, state in self.segment_state.items():
                city_name = state["city"]

                # Weather coupling check: Rain increases congestion & incident risk
                rain_factor = 1.0
                if city_state_mgr:
                    live_state = city_state_mgr.get_live_city_state()
                    cs_summary = live_state.get("city_summaries", {}).get(city_name, {})
                    w_dict = cs_summary.get("weather") if isinstance(cs_summary, dict) and cs_summary.get("weather") else {}
                    w_cond = str(w_dict.get("condition", "")).lower()
                    if "rain" in w_cond or "thunderstorm" in w_cond:
                        rain_factor = 1.45

                # Smooth state transition (no teleporting values)
                target_congestion = min(0.95, (self.rng.uniform(0.20, 0.40) * peak_factor * rain_factor))

                # Handle incident Poisson state machine
                if state["active_incident"]:
                    state["incident_duration_ticks"] -= 1
                    if state["incident_duration_ticks"] <= 0:
                        state["active_incident"] = False
                    else:
                        target_congestion = min(0.98, target_congestion + 0.35)
                else:
                    # 3% chance of spontaneous incident during peak hours
                    if peak_factor > 1.4 and self.rng.random() < 0.03:
                        state["active_incident"] = True
                        state["incident_duration_ticks"] = self.rng.randint(3, 8)
                        target_congestion = min(0.98, target_congestion + 0.35)

                # Smoothly adjust congestion towards target
                current = state["congestion_level"]
                state["congestion_level"] = round(current + (target_congestion - current) * 0.35, 2)

                # Derive average speed from congestion
                max_speed = 50.0
                speed = max(8.0, max_speed * (1.0 - state["congestion_level"] * 0.75))
                state["avg_speed_kmh"] = round(speed, 1)

                vehicle_count = int(state["capacity"] * state["congestion_level"])
                incident_prob = round(min(0.99, state["congestion_level"] * 0.8), 2)
                severity = "CRITICAL" if state["congestion_level"] > 0.85 else ("HIGH" if state["congestion_level"] > 0.65 else ("MODERATE" if state["congestion_level"] > 0.40 else "LOW"))

                self.status = "LIVE"
                self.last_updated = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")

                event = create_city_event(
                    source="traffic_simulation",
                    event_type="traffic_congestion",
                    latitude=state["base_lat"] + state["offset_lat"],
                    longitude=state["base_lon"] + state["offset_lon"],
                    severity=severity,
                    data={
                        "city": city_name,
                        "state": state["state"],
                        "road_segment": state["segment"],
                        "congestion_level": state["congestion_level"],
                        "average_speed": state["avg_speed_kmh"],
                        "vehicle_count": vehicle_count,
                        "incident_probability": incident_prob,
                        "active_incident": state["active_incident"],
                        "mode": "SIMULATED",
                        "source": "traffic_simulation"
                    }
                )
                yield event

            time.sleep(self.interval)
