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
from .base import DataSource
from .models import create_city_event

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

logger = logging.getLogger(__name__)

# Shared Global Thread-Safe Queue for Webhook Events
WEBHOOK_EVENT_QUEUE: queue.Queue = queue.Queue()

class EventSchema(pw.Schema):
    timestamp: str
    source: str
    data: pw.Json
    location: pw.Json

class WeatherSource(DataSource):
    name = "weather_api"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lat = self.config.get('location', {}).get('lat', 40.7128)
        self.lon = self.config.get('location', {}).get('lon', -74.0060)
        self.poll_interval = self.config.get('data_sources', {}).get('weather', {}).get('poll_interval', 60)
        self.status = "INITIALIZING"
        self.last_updated = "N/A"

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)

    def _stream(self):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&current_weather=true"
        while True:
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
                        latitude=self.lat,
                        longitude=self.lon,
                        severity="LOW" if temp < 35 else "MODERATE",
                        data={
                            "temperature": temp,
                            "wind_speed": wind,
                            "weather_code": code,
                            "condition": self._get_weather_condition(code)
                        }
                    )
                    logger.info(f"[Weather API] Ingested live weather: {temp}°C, {self._get_weather_condition(code)}")
                    yield event
                else:
                    logger.warning(f"[Weather API] HTTP error: {response.status_code}")
                    self.status = "OFFLINE"
            except Exception as e:
                logger.error(f"[Weather API] Connection failed: {e}")
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
        self.lat = self.config.get('location', {}).get('lat', 40.7128)
        self.lon = self.config.get('location', {}).get('lon', -74.0060)
        self.poll_interval = self.config.get('data_sources', {}).get('air_quality', {}).get('poll_interval', 90)
        self.status = "INITIALIZING"
        self.last_updated = "N/A"

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)

    def _stream(self):
        url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={self.lat}&longitude={self.lon}&current=us_aqi,pm10,pm2_5,nitrogen_dioxide,ozone"
        while True:
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
                        latitude=self.lat,
                        longitude=self.lon,
                        severity=severity,
                        data={
                            "air_quality_index": aqi,
                            "pm2_5": pm25,
                            "pm10": pm10,
                            "nitrogen_dioxide": no2,
                            "anomaly": aqi > 100,
                            "anomaly_type": "air_quality_anomaly" if aqi > 100 else None,
                            "anomaly_description": f"Elevated AQI detected: {aqi}" if aqi > 100 else None
                        }
                    )
                    logger.info(f"[Air Quality API] Ingested live AQI: {aqi} ({severity})")
                    yield event
                else:
                    self.status = "OFFLINE"
            except Exception as e:
                logger.error(f"[Air Quality API] Connection failed: {e}")
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
        return pw.io.python.read(self._stream, schema=self.schema)

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
        return pw.io.python.read(self._stream, schema=self.schema)

    def _stream(self):
        logger.info("[Webhook Ingestion] Ready to receive POST events via WEBHOOK_EVENT_QUEUE.")
        while True:
            try:
                event_payload = WEBHOOK_EVENT_QUEUE.get(timeout=1.0)
                if event_payload:
                    self.last_updated = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")
                    logger.info(f"[Webhook Ingestion] Dispatched webhook event: {event_payload.get('event_type')}")
                    yield event_payload
            except queue.Empty:
                pass
            time.sleep(0.5)

def ingest_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and normalizes an external HTTP POST payload into a CityEvent and queues it for Pathway.
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
    return event
