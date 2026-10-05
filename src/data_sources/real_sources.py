"""
Real External Data Connectors for Phase 3.
Implements live HTTP REST connectors (Open-Meteo Weather, Air Quality), GTFS Transit interface,
and HTTP Webhook event stream ingestion.
"""

import time
import datetime
import logging
import requests
import queue
from typing import Dict, Any, Optional
from .base import DataSource, GeneratorConnectorSubject
from .models import create_city_event

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

logger = logging.getLogger(__name__)

# Shared Global Thread-Safe Queue for Webhook Events
WEBHOOK_EVENT_QUEUE: queue.Queue = queue.Queue()

# Centralized South India Metropolitan Cities Configuration
SOUTH_INDIA_CITIES = [
    {"city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707},
    {"city": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lon": 76.9558},
    {"city": "Madurai", "state": "Tamil Nadu", "lat": 9.9252, "lon": 78.1198},
    {"city": "Salem", "state": "Tamil Nadu", "lat": 11.6643, "lon": 78.1460},
    {"city": "Tiruchirappalli", "state": "Tamil Nadu", "lat": 10.7905, "lon": 78.7047},
    {"city": "Tiruppur", "state": "Tamil Nadu", "lat": 11.1085, "lon": 77.3411},
    {"city": "Erode", "state": "Tamil Nadu", "lat": 11.3410, "lon": 77.7172},
    {"city": "Vellore", "state": "Tamil Nadu", "lat": 12.9165, "lon": 79.1325},

    {"city": "Kochi", "state": "Kerala", "lat": 9.9312, "lon": 76.2673},
    {"city": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lon": 76.9366},
    {"city": "Kozhikode", "state": "Kerala", "lat": 11.2588, "lon": 75.7804},
    {"city": "Thrissur", "state": "Kerala", "lat": 10.5276, "lon": 76.2144},
    {"city": "Kollam", "state": "Kerala", "lat": 8.8932, "lon": 76.6141},
    {"city": "Kannur", "state": "Kerala", "lat": 11.8745, "lon": 75.3704},

    {"city": "Visakhapatnam", "state": "Andhra Pradesh", "lat": 17.6868, "lon": 83.2185},
    {"city": "Vijayawada", "state": "Andhra Pradesh", "lat": 16.5062, "lon": 80.6480},
    {"city": "Guntur", "state": "Andhra Pradesh", "lat": 16.3067, "lon": 80.4365},
    {"city": "Tirupati", "state": "Andhra Pradesh", "lat": 13.6288, "lon": 79.4192},
    {"city": "Nellore", "state": "Andhra Pradesh", "lat": 14.4426, "lon": 79.9865},
    {"city": "Kurnool", "state": "Andhra Pradesh", "lat": 15.8281, "lon": 78.0373}
]

class EventSchema(pw.Schema):
    timestamp: str
    source: str
    data: pw.Json
    location: pw.Json

class WeatherSource(DataSource):
    name = "weather_api"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cities = SOUTH_INDIA_CITIES
        self.poll_interval = self.config.get('data_sources', {}).get('weather', {}).get('poll_interval', 60)
        self.status = "INITIALIZING"
        self.last_updated = "N/A"

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

    def _stream(self):
        while True:
            for c in self.cities:
                url = f"https://api.open-meteo.com/v1/forecast?latitude={c['lat']}&longitude={c['lon']}&current_weather=true"
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        cw = response.json().get('current_weather', {})
                        temp = cw.get('temperature', 20.0)
                        wind = cw.get('windspeed', 10.0)
                        code = cw.get('weathercode', 0)
                        
                        self.status = "LIVE"
                        self.last_updated = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")
                        
                        event = create_city_event(
                            source="weather_api",
                            event_type="weather_update",
                            latitude=c['lat'],
                            longitude=c['lon'],
                            severity="LOW" if temp < 35 else "MODERATE",
                            data={
                                "city": c['city'],
                                "state": c['state'],
                                "temperature": temp,
                                "wind_speed": wind,
                                "weather_code": code,
                                "condition": self._get_weather_condition(code)
                            }
                        )
                        logger.info(f"[Weather API] Ingested live weather for {c['city']}: {temp}°C, {self._get_weather_condition(code)}")
                        yield event
                    else:
                        logger.warning(f"[Weather API] HTTP error for {c['city']}: {response.status_code}")
                except Exception as e:
                    logger.error(f"[Weather API] Connection failed for {c['city']}: {e}")
                    self.status = "OFFLINE"
            
            time.sleep(self.poll_interval)

    @staticmethod
    def _get_weather_condition(code: int) -> str:
        conditions = {0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast", 45: "Fog", 61: "Rain Showers", 95: "Thunderstorm"}
        return conditions.get(code, "Clear")

class AirQualitySource(DataSource):
    name = "air_quality_api"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cities = SOUTH_INDIA_CITIES
        self.poll_interval = self.config.get('data_sources', {}).get('air_quality', {}).get('poll_interval', 90)
        self.status = "INITIALIZING"
        self.last_updated = "N/A"

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

    def _stream(self):
        while True:
            for c in self.cities:
                url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={c['lat']}&longitude={c['lon']}&current=us_aqi,pm10,pm2_5,nitrogen_dioxide,ozone"
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        curr = response.json().get('current', {})
                        aqi = curr.get('us_aqi', 50)
                        pm25 = curr.get('pm2_5', 12.0)
                        pm10 = curr.get('pm10', 20.0)
                        no2 = curr.get('nitrogen_dioxide', 15.0)

                        self.status = "LIVE"
                        self.last_updated = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")

                        severity = "CRITICAL" if aqi > 150 else ("HIGH" if aqi > 100 else ("MODERATE" if aqi > 50 else "LOW"))

                        event = create_city_event(
                            source="air_quality_api",
                            event_type="air_quality_update",
                            latitude=c['lat'],
                            longitude=c['lon'],
                            severity=severity,
                            data={
                                "city": c['city'],
                                "state": c['state'],
                                "air_quality_index": aqi,
                                "pm2_5": pm25,
                                "pm10": pm10,
                                "nitrogen_dioxide": no2,
                                "anomaly": aqi > 100,
                                "anomaly_type": "air_quality_anomaly" if aqi > 100 else None,
                                "anomaly_description": f"Elevated AQI detected in {c['city']}: {aqi}" if aqi > 100 else None
                            }
                        )
                        logger.info(f"[Air Quality API] Ingested live AQI for {c['city']}: {aqi} ({severity})")
                        yield event
                    else:
                        logger.warning(f"[Air Quality API] HTTP error for {c['city']}: {response.status_code}")
                except Exception as e:
                    logger.error(f"[Air Quality API] Connection failed for {c['city']}: {e}")
                    self.status = "OFFLINE"
            
            time.sleep(self.poll_interval)

class GTFSTransitSource(DataSource):
    name = "gtfs_transit_api"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.feed_url = self.config.get('data_sources', {}).get('transit', {}).get('feed_url')
        self.status = "LIVE" if self.feed_url else "NOT CONFIGURED"
        self.last_updated = "N/A"

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

    def _stream(self):
        if not self.feed_url:
            logger.info("[GTFS Transit API] No GTFS feed_url configured. Connector marked NOT CONFIGURED.")
            # Emit single initial notice event and pause
            yield create_city_event(
                source="gtfs_transit_api",
                event_type="transit_status",
                latitude=self.config.get('location', {}).get('lat', 40.7128),
                longitude=self.config.get('location', {}).get('lon', -74.0060),
                severity="LOW",
                data={"status": "NOT CONFIGURED", "message": "Set GTFS_FEED_URL in .env to activate live transit streaming."}
            )
            while True:
                time.sleep(300)

        while True:
            try:
                resp = requests.get(self.feed_url, timeout=5)
                if resp.status_code == 200:
                    self.status = "LIVE"
                    self.last_updated = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")
                    yield create_city_event(
                        source="gtfs_transit_api",
                        event_type="transit_feed_update",
                        latitude=self.config.get('location', {}).get('lat', 40.7128),
                        longitude=self.config.get('location', {}).get('lon', -74.0060),
                        severity="LOW",
                        data={"feed_status": "active", "content_length": len(resp.content)}
                    )
            except Exception as e:
                logger.warning(f"[GTFS Transit API] Fetch failed: {e}")
                self.status = "OFFLINE"
            time.sleep(60)

class WebhookSource(DataSource):
    name = "webhook_api"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.status = "READY"
        self.last_updated = "Listening for HTTP events"

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

    def _stream(self):
        logger.info("[Webhook Ingestion] Ready to receive POST events via WEBHOOK_EVENT_QUEUE.")
        while True:
            try:
                event_payload = WEBHOOK_EVENT_QUEUE.get(timeout=0.5)
                if event_payload:
                    self.last_updated = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")
                    logger.info(f"[Webhook Ingestion] Dispatched webhook event into Pathway stream: {event_payload.get('data', {}).get('event_type')}")
                    yield event_payload
            except queue.Empty:
                pass
            time.sleep(0.1)

def ingest_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and normalizes an external HTTP POST payload into a CityEvent,
    queues it for Pathway streaming pipeline processing.
    """
    if not isinstance(payload, dict):
        raise ValueError("Webhook payload must be a valid JSON dictionary.")

    event_type = payload.get("event_type", "external_alert")
    lat = payload.get("latitude", payload.get("location", {}).get("lat", 40.7128))
    lon = payload.get("longitude", payload.get("location", {}).get("lon", -74.0060))
    severity = payload.get("severity", "HIGH").upper()
    source = payload.get("source", "external_webhook")
    data_content = payload.get("data", payload)

    event = create_city_event(
        source=source,
        event_type=event_type,
        latitude=lat,
        longitude=lon,
        severity=severity,
        data=data_content,
        event_id=payload.get("event_id"),
        timestamp=payload.get("timestamp")
    )
    WEBHOOK_EVENT_QUEUE.put(event)

    # Stream event into active Pathway tables
    pushed = False
    try:
        from ..pathway_compat import _ACTIVE_STREAMS
        for item in list(_ACTIVE_STREAMS):
            tbl = item[0] if isinstance(item, tuple) else item
            subject = item[1] if isinstance(item, tuple) else getattr(tbl, "generator", None)
            if subject and getattr(subject, "source", None) and isinstance(subject.source, WebhookSource):
                tbl.publish(event)
                pushed = True
    except Exception as e:
        logger.debug(f"Pathway stream direct publish fallback: {e}")

    # Fallback for standalone unit tests when no Pathway pipeline streams are active
    if not pushed:
        try:
            from ..pathway_compat import _ACTIVE_STREAMS
            if not _ACTIVE_STREAMS:
                from ..processing.shared_state import ingest_runtime_event
                ingest_runtime_event(event)
        except Exception:
            pass

    return event


