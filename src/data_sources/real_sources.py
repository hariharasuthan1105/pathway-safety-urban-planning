"""
Real External Data Connectors for South India Urban Intelligence.
Implements live HTTP REST connectors (Open-Meteo Weather, Air Quality) with batched multi-coordinate
polling, 429 backoff, observation-time tracking, stale-cache resilience, GTFS-Realtime decoder,
and HTTP Webhook event stream ingestion.
"""

import os
import time
import datetime
import logging
import requests
import queue
import math
from typing import Dict, Any, Optional, List
from .base import DataSource, GeneratorConnectorSubject
from .models import create_city_event

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

try:
    from google.transit import gtfs_realtime_pb2
    HAS_GTFS_PB = True
except (ImportError, AttributeError):
    gtfs_realtime_pb2 = None
    HAS_GTFS_PB = False

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

def _normalize_batch_response(raw_data: Any) -> List[Dict[str, Any]]:
    """Normalizes single-location (dict) and multi-location (list) API responses."""
    if isinstance(raw_data, list):
        return [item for item in raw_data if isinstance(item, dict)]
    elif isinstance(raw_data, dict):
        return [raw_data]
    return []

class WeatherSource(DataSource):
    name = "weather_api"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cities = list(SOUTH_INDIA_CITIES)
        raw_interval = os.getenv("WEATHER_POLL_INTERVAL") or self.config.get('data_sources', {}).get('weather', {}).get('poll_interval', 60)
        try:
            self.poll_interval = int(raw_interval)
        except (ValueError, TypeError):
            self.poll_interval = 60
        self.batch_size = int(os.getenv("WEATHER_BATCH_SIZE", "20"))
        self.status = "INITIALIZING"
        self.last_updated = "N/A"
        self.last_checked_at = None
        self.retry_count = 0
        self.base_backoff = 2.0
        self.cached_observations: Dict[str, Dict[str, Any]] = {}

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

    def _handle_backoff(self, response: Optional[requests.Response] = None):
        self.retry_count += 1
        retry_after = None
        if response is not None and response.status_code == 429:
            raw_header = response.headers.get("Retry-After")
            if raw_header:
                try:
                    retry_after = float(raw_header)
                except ValueError:
                    pass
        if retry_after is not None and retry_after > 0:
            sleep_time = min(retry_after, 60.0)
        else:
            sleep_time = min(60.0, self.base_backoff * (2 ** min(self.retry_count, 5)))
        logger.warning(f"[{self.name}] Applying backoff ({sleep_time:.1f}s) after attempt {self.retry_count}")
        time.sleep(sleep_time)

    def _stream(self):
        while True:
            # Chunk cities into batched multi-coordinate requests
            chunks = [self.cities[i:i + self.batch_size] for i in range(0, len(self.cities), self.batch_size)] if self.cities else []
            for chunk in chunks:
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                self.last_checked_at = now_utc.isoformat()

                lat_str = ",".join(str(c['lat']) for c in chunk)
                lon_str = ",".join(str(c['lon']) for c in chunk)
                # Supports modern Open-Meteo current parameters as well as legacy/mock current_weather
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat_str}&longitude={lon_str}&current=temperature_2m,wind_speed_10m,weather_code&current_weather=true"

                try:
                    response = requests.get(url, timeout=8)
                    if response.status_code == 200:
                        self.retry_count = 0
                        raw_json = response.json()
                        results = _normalize_batch_response(raw_json)

                        batch_events = []
                        for idx, c in enumerate(chunk):
                            if idx >= len(results):
                                break
                            item = results[idx]
                            # Resolve current weather from either modern or legacy/mock format
                            cw = item.get('current') or item.get('current_weather') or {}
                            temp = cw.get('temperature_2m') if 'temperature_2m' in cw else cw.get('temperature')
                            wind = cw.get('wind_speed_10m') if 'wind_speed_10m' in cw else cw.get('windspeed')
                            code = cw.get('weather_code') if 'weather_code' in cw else cw.get('weathercode')
                            obs_time = cw.get('time') or now_utc.isoformat()

                            if temp is None or code is None:
                                logger.warning(f"[Weather API] Incomplete weather values for {c['city']}; skipping single city observation.")
                                continue

                            received_at = now_utc.isoformat()
                            condition_text = self._get_weather_condition(int(code))
                            obs_payload = {
                                "city": c['city'],
                                "state": c['state'],
                                "temperature": temp,
                                "wind_speed": wind,
                                "weather_code": code,
                                "condition": condition_text,
                                "observed_at": obs_time,
                                "received_at": received_at
                            }
                            # Cache successful observation per city
                            self.cached_observations[c['city']] = obs_payload

                            event = create_city_event(
                                source="weather_api",
                                event_type="weather_update",
                                latitude=c['lat'],
                                longitude=c['lon'],
                                severity="LOW" if temp < 35 else "MODERATE",
                                data=obs_payload,
                                timestamp=received_at
                            )
                            batch_events.append((c['city'], temp, condition_text, event))

                        if batch_events:
                            self.status = "LIVE"
                            self.last_updated = now_utc.strftime("%H:%M:%S UTC")
                            for city_name, temp_val, cond_val, ev in batch_events:
                                logger.info(f"[Weather API] Ingested live weather for {city_name}: {temp_val}°C, {cond_val}")
                                yield ev

                    elif response.status_code == 429:
                        self.status = "DEGRADED"
                        logger.warning(f"[Weather API] Rate limited (HTTP 429) by Open-Meteo. Backing off.")
                        self._handle_backoff(response)
                    else:
                        self.status = "DEGRADED"
                        logger.warning(f"[Weather API] HTTP error: {response.status_code}")
                except requests.RequestException as e:
                    self.status = "OFFLINE"
                    logger.error(f"[Weather API] Connection failed: {e}")
                except Exception as e:
                    self.status = "DEGRADED"
                    logger.error(f"[Weather API] Unexpected parsing error: {e}")

            time.sleep(self.poll_interval)

    @staticmethod
    def _get_weather_condition(code: int) -> str:
        conditions = {
            0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing Rime Fog",
            51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
            61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
            71: "Slight Snow Fall", 80: "Rain Showers", 81: "Moderate Showers",
            82: "Violent Rain Showers", 95: "Thunderstorm"
        }
        return conditions.get(code, "Unclassified weather code")

class AirQualitySource(DataSource):
    name = "air_quality_api"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cities = list(SOUTH_INDIA_CITIES)
        raw_interval = os.getenv("AIR_QUALITY_POLL_INTERVAL") or self.config.get('data_sources', {}).get('air_quality', {}).get('poll_interval', 90)
        try:
            self.poll_interval = int(raw_interval)
        except (ValueError, TypeError):
            self.poll_interval = 90
        self.batch_size = int(os.getenv("AIR_QUALITY_BATCH_SIZE", "20"))
        self.status = "INITIALIZING"
        self.last_updated = "N/A"
        self.last_checked_at = None
        self.retry_count = 0
        self.base_backoff = 2.0
        self.cached_observations: Dict[str, Dict[str, Any]] = {}

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

    def _handle_backoff(self, response: Optional[requests.Response] = None):
        self.retry_count += 1
        retry_after = None
        if response is not None and response.status_code == 429:
            raw_header = response.headers.get("Retry-After")
            if raw_header:
                try:
                    retry_after = float(raw_header)
                except ValueError:
                    pass
        if retry_after is not None and retry_after > 0:
            sleep_time = min(retry_after, 60.0)
        else:
            sleep_time = min(60.0, self.base_backoff * (2 ** min(self.retry_count, 5)))
        logger.warning(f"[{self.name}] Applying backoff ({sleep_time:.1f}s) after attempt {self.retry_count}")
        time.sleep(sleep_time)

    def _stream(self):
        while True:
            chunks = [self.cities[i:i + self.batch_size] for i in range(0, len(self.cities), self.batch_size)] if self.cities else []
            for chunk in chunks:
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                self.last_checked_at = now_utc.isoformat()

                lat_str = ",".join(str(c['lat']) for c in chunk)
                lon_str = ",".join(str(c['lon']) for c in chunk)
                url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat_str}&longitude={lon_str}&current=us_aqi,pm10,pm2_5,nitrogen_dioxide,ozone"

                try:
                    response = requests.get(url, timeout=8)
                    if response.status_code == 200:
                        self.retry_count = 0
                        raw_json = response.json()
                        results = _normalize_batch_response(raw_json)

                        batch_events = []
                        for idx, c in enumerate(chunk):
                            if idx >= len(results):
                                break
                            item = results[idx]
                            curr = item.get('current') or {}
                            aqi = curr.get('us_aqi')
                            pm25 = curr.get('pm2_5')
                            pm10 = curr.get('pm10')
                            no2 = curr.get('nitrogen_dioxide')
                            ozone = curr.get('ozone')
                            obs_time = curr.get('time') or now_utc.isoformat()

                            if aqi is None:
                                logger.warning(f"[Air Quality API] Missing AQI value for {c['city']}; skipping single city observation.")
                                continue

                            received_at = now_utc.isoformat()
                            severity = "CRITICAL" if aqi > 150 else ("HIGH" if aqi > 100 else ("MODERATE" if aqi > 50 else "LOW"))

                            obs_payload = {
                                "city": c['city'],
                                "state": c['state'],
                                "air_quality_index": aqi,
                                "pm2_5": pm25,
                                "pm10": pm10,
                                "nitrogen_dioxide": no2,
                                "ozone": ozone,
                                "observed_at": obs_time,
                                "received_at": received_at,
                                "anomaly": aqi > 100,
                                "anomaly_type": "air_quality_anomaly" if aqi > 100 else None,
                                "anomaly_description": f"Elevated AQI detected in {c['city']}: {aqi}" if aqi > 100 else None
                            }
                            # Cache successful observation per city
                            self.cached_observations[c['city']] = obs_payload

                            event = create_city_event(
                                source="air_quality_api",
                                event_type="air_quality_update",
                                latitude=c['lat'],
                                longitude=c['lon'],
                                severity=severity,
                                data=obs_payload,
                                timestamp=received_at
                            )
                            batch_events.append((c['city'], aqi, severity, event))

                        if batch_events:
                            self.status = "LIVE"
                            self.last_updated = now_utc.strftime("%H:%M:%S UTC")
                            for city_name, aqi_val, sev_val, ev in batch_events:
                                logger.info(f"[Air Quality API] Ingested live AQI for {city_name}: {aqi_val} ({sev_val})")
                                yield ev

                    elif response.status_code == 429:
                        self.status = "DEGRADED"
                        logger.warning(f"[Air Quality API] Rate limited (HTTP 429) by Open-Meteo. Backing off.")
                        self._handle_backoff(response)
                    else:
                        self.status = "DEGRADED"
                        logger.warning(f"[Air Quality API] HTTP error: {response.status_code}")
                except requests.RequestException as e:
                    self.status = "OFFLINE"
                    logger.error(f"[Air Quality API] Connection failed: {e}")
                except Exception as e:
                    self.status = "DEGRADED"
                    logger.error(f"[Air Quality API] Unexpected parsing error: {e}")

            time.sleep(self.poll_interval)

class GTFSTransitSource(DataSource):
    """
    Honest GTFS-Realtime Adapter (§4).
    If GTFS_FEED_URL is unconfigured, stays NOT_CONFIGURED without emitting fake events.
    If configured, decodes FeedMessage entities (TripUpdates, VehiclePositions, Alerts).
    Validates timestamps to reject stale entities (> 900s).
    """
    name = "gtfs_transit_api"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.feed_url = (self.config.get('data_sources', {}).get('transit', {}).get('feed_url') or os.getenv('GTFS_FEED_URL') or '').strip()
        self.poll_interval = int(os.getenv("GTFS_POLL_INTERVAL", "60"))
        self.status = "READY" if self.feed_url else "NOT_CONFIGURED"
        self.last_checked_at = None
        self.last_updated = "N/A"

    def _define_schema(self):
        return EventSchema

    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

    def _decode_feed_entities(self, content_data: Any) -> List[Dict[str, Any]]:
        """
        Decodes GTFS-Realtime FeedMessage entities from JSON representation or parsed protobuf.
        Rejects entities with timestamps older than 15 minutes (stale threshold).
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        stale_threshold_seconds = 900
        decoded_events = []

        if isinstance(content_data, dict):
            entities = content_data.get("entity") or content_data.get("entities") or []
            feed_ts = content_data.get("header", {}).get("timestamp")

            for ent in entities:
                if not isinstance(ent, dict):
                    continue
                ent_id = str(ent.get("id", "gtfs_ent"))

                # 1. Trip Update
                if "trip_update" in ent:
                    tu = ent["trip_update"]
                    trip = tu.get("trip", {})
                    delays = [stu.get("arrival", {}).get("delay", 0) for stu in tu.get("stop_time_update", [])]
                    max_delay = max(delays) if delays else 0
                    delay_minutes = round(max_delay / 60.0, 1)

                    ent_time = tu.get("timestamp") or feed_ts
                    if ent_time and (now.timestamp() - float(ent_time) > stale_threshold_seconds):
                        continue  # Discard stale trip update

                    severity = "CRITICAL" if delay_minutes > 30 else ("HIGH" if delay_minutes > 15 else "MODERATE" if delay_minutes > 5 else "LOW")
                    decoded_events.append(create_city_event(
                        source="gtfs_transit_api",
                        event_type="transit_trip_update",
                        latitude=13.0827,  # Default regional transit anchor
                        longitude=80.2707,
                        severity=severity,
                        data={
                            "event_id": f"gtfs_tu_{ent_id}",
                            "trip_id": trip.get("trip_id"),
                            "route_id": trip.get("route_id"),
                            "delay_minutes": delay_minutes,
                            "mode": "LIVE",
                            "source": "gtfs_transit_api"
                        }
                    ))

                # 2. Vehicle Position
                elif "vehicle" in ent:
                    veh = ent["vehicle"]
                    pos = veh.get("position", {})
                    lat = pos.get("latitude")
                    lon = pos.get("longitude")
                    if lat is not None and lon is not None:
                        ent_time = veh.get("timestamp") or feed_ts
                        if ent_time and (now.timestamp() - float(ent_time) > stale_threshold_seconds):
                            continue

                        decoded_events.append(create_city_event(
                            source="gtfs_transit_api",
                            event_type="transit_vehicle_position",
                            latitude=float(lat),
                            longitude=float(lon),
                            severity="LOW",
                            data={
                                "event_id": f"gtfs_veh_{ent_id}",
                                "vehicle_id": veh.get("vehicle", {}).get("id", ent_id),
                                "speed_kmh": round(pos.get("speed", 0.0) * 3.6, 1) if pos.get("speed") is not None else None,
                                "mode": "LIVE",
                                "source": "gtfs_transit_api"
                            }
                        ))

                # 3. Service Alert
                elif "alert" in ent:
                    al = ent["alert"]
                    header = al.get("header_text", {}).get("translation", [{}])[0].get("text", "Transit service alert") if isinstance(al.get("header_text"), dict) else str(al.get("header_text", "Transit Alert"))
                    decoded_events.append(create_city_event(
                        source="gtfs_transit_api",
                        event_type="transit_service_alert",
                        latitude=13.0827,
                        longitude=80.2707,
                        severity="HIGH",
                        data={
                            "event_id": f"gtfs_alt_{ent_id}",
                            "alert_text": header,
                            "cause": al.get("cause", "UNKNOWN_CAUSE"),
                            "effect": al.get("effect", "UNKNOWN_EFFECT"),
                            "mode": "LIVE",
                            "source": "gtfs_transit_api"
                        }
                    ))

        return decoded_events

    def _decode_protobuf_bytes(self, content_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Decodes binary GTFS-Realtime FeedMessage protobuf entities.
        """
        if not HAS_GTFS_PB or not content_bytes:
            return []
        try:
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(content_bytes)
        except Exception as e:
            logger.warning(f"[GTFS Transit API] Protobuf parse error: {e}")
            return []

        feed_dict = {
            "header": {
                "gtfs_realtime_version": feed.header.gtfs_realtime_version,
                "timestamp": feed.header.timestamp if feed.header.HasField("timestamp") else None
            },
            "entity": []
        }
        for ent in feed.entity:
            ent_dict: Dict[str, Any] = {"id": ent.id}
            if ent.HasField("trip_update"):
                tu = ent.trip_update
                ent_dict["trip_update"] = {
                    "trip": {
                        "trip_id": tu.trip.trip_id if tu.trip.HasField("trip_id") else None,
                        "route_id": tu.trip.route_id if tu.trip.HasField("route_id") else None,
                    },
                    "timestamp": tu.timestamp if tu.HasField("timestamp") else None,
                    "stop_time_update": [
                        {"arrival": {"delay": stu.arrival.delay}}
                        for stu in tu.stop_time_update if stu.HasField("arrival") and stu.arrival.HasField("delay")
                    ]
                }
            elif ent.HasField("vehicle"):
                v = ent.vehicle
                ent_dict["vehicle"] = {
                    "vehicle": {"id": v.vehicle.id if v.vehicle.HasField("id") else ent.id},
                    "position": {
                        "latitude": v.position.latitude if v.position.HasField("latitude") else None,
                        "longitude": v.position.longitude if v.position.HasField("longitude") else None,
                        "speed": v.position.speed if v.position.HasField("speed") else None,
                    },
                    "timestamp": v.timestamp if v.HasField("timestamp") else None
                }
            elif ent.HasField("alert"):
                al = ent.alert
                header_text = al.header_text.translation[0].text if al.header_text.translation else "Alert"
                ent_dict["alert"] = {
                    "header_text": header_text,
                    "cause": str(al.cause),
                    "effect": str(al.effect),
                }
            feed_dict["entity"].append(ent_dict)

        return self._decode_feed_entities(feed_dict)

    def _stream(self):
        yield from ()
        if not self.feed_url:
            logger.info("[GTFS Transit API] No GTFS feed_url configured. Staying in NOT_CONFIGURED state.")
            return

        while True:
            self.last_checked_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            try:
                resp = requests.get(
                    self.feed_url,
                    timeout=8,
                    headers={"Accept": "application/x-protobuf, application/octet-stream, application/json, text/plain"}
                )
                if resp.status_code == 200:
                    self.status = "REACHABLE"
                    parsed_data = None
                    try:
                        parsed_data = resp.json()
                    except Exception:
                        pass

                    decoded_events = []
                    if parsed_data:
                        decoded_events = self._decode_feed_entities(parsed_data)
                    elif HAS_GTFS_PB and resp.content:
                        decoded_events = self._decode_protobuf_bytes(resp.content)

                    if decoded_events:
                        self.status = "LIVE"
                        self.last_updated = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")
                        for ev in decoded_events:
                            yield ev
                    else:
                        # Reachability probe without decoded entities: remains REACHABLE with last_updated="N/A"
                        logger.debug("[GTFS Transit API] HTTP reachability verified; 0 decoded feed entities in batch.")
                else:
                    self.status = "DEGRADED"
                    logger.warning(f"[GTFS Transit API] Feed HTTP error: {resp.status_code}")
            except requests.RequestException as e:
                self.status = "OFFLINE"
                logger.warning(f"[GTFS Transit API] Feed request failed: {e}")
            except Exception as e:
                self.status = "DEGRADED"
                logger.error(f"[GTFS Transit API] Feed decode failure: {e}")

            time.sleep(self.poll_interval)

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
    lat = payload.get("latitude", payload.get("location", {}).get("lat"))
    lon = payload.get("longitude", payload.get("location", {}).get("lon"))

    # Coordinate boundary validation
    if lat is not None and lon is not None:
        try:
            f_lat, f_lon = float(lat), float(lon)
            if not (-90.0 <= f_lat <= 90.0 and -180.0 <= f_lon <= 180.0):
                raise ValueError(f"Invalid coordinate range: latitude must be [-90, 90], longitude [-180, 180]. Got ({f_lat}, {f_lon})")
            lat, lon = f_lat, f_lon
        except (ValueError, TypeError) as e:
            if "range" in str(e):
                raise
            raise ValueError(f"Coordinates must be numeric: {e}")

    severity = str(payload.get("severity", "HIGH")).upper()
    source = payload.get("source", "external_webhook")
    data_content = payload.get("data", payload)
    if not isinstance(data_content, dict):
        data_content = {"raw_content": data_content}

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

    # A running connector consumes the queue exactly once. Standalone tests
    # without a pipeline still feed the shared runtime directly.
    from ..pathway_compat import IS_NATIVE_PATHWAY
    if IS_NATIVE_PATHWAY:
        WEBHOOK_EVENT_QUEUE.put(event)
    else:
        from ..pathway_compat import _ACTIVE_STREAMS
        if _ACTIVE_STREAMS:
            WEBHOOK_EVENT_QUEUE.put(event)
        else:
            from ..processing.shared_state import ingest_runtime_event
            ingest_runtime_event(event)

    return event
