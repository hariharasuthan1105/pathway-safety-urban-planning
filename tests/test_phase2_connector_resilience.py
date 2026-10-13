"""
Regression tests for Phase 2 (Weather & Air Quality connector resilience)
and Phase 4 (GTFS-Realtime decoding & traffic adapter specifications).
"""

import time
import datetime
import pytest
from unittest.mock import patch, MagicMock
import requests

from src.data_sources.real_sources import WeatherSource, AirQualitySource, GTFSTransitSource, SOUTH_INDIA_CITIES
from src.data_sources.traffic_adapters import TomTomTrafficConnector, GoogleTrafficConnector
from src.processing.shared_state import reset_shared_state, get_shared_city_state_manager

class StopPolling(BaseException):
    """Helper to break out of infinite polling loop in tests."""
    pass

def test_weather_batched_multi_coordinate_request():
    ws = WeatherSource({})
    ws.cities = SOUTH_INDIA_CITIES[:2]  # Chennai and Coimbatore
    ws.batch_size = 2

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = [
        {
            "latitude": 13.08, "longitude": 80.27,
            "current": {"temperature_2m": 31.5, "wind_speed_10m": 12.0, "weather_code": 1, "time": "2026-10-13T04:00"}
        },
        {
            "latitude": 11.02, "longitude": 76.96,
            "current": {"temperature_2m": 27.0, "wind_speed_10m": 8.5, "weather_code": 2, "time": "2026-10-13T04:00"}
        }
    ]

    with patch("src.data_sources.real_sources.requests.get", return_value=mock_resp) as mock_get, \
         patch("src.data_sources.real_sources.time.sleep", side_effect=StopPolling):
        stream = ws._stream()
        ev1 = next(stream)
        ev2 = next(stream)

    assert mock_get.call_count == 1
    # Confirm batched multi-coordinate parameters in request URL
    call_url = mock_get.call_args[0][0]
    assert "13.0827" in call_url and "11.0168" in call_url

    assert ev1["source"] == "weather_api"
    assert ev1["data"]["city"] == "Chennai"
    assert ev1["data"]["temperature"] == 31.5
    assert ev1["data"]["observed_at"] == "2026-10-13T04:00"
    assert "received_at" in ev1["data"]

    assert ev2["data"]["city"] == "Coimbatore"
    assert ev2["data"]["temperature"] == 27.0
    assert ws.status == "LIVE"
    assert ws.cached_observations["Chennai"]["temperature"] == 31.5
    assert ws.cached_observations["Coimbatore"]["temperature"] == 27.0

def test_weather_http_429_backoff_and_retry_after():
    ws = WeatherSource({})
    ws.cities = ws.cities[:1]

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "4.5"}

    with patch("src.data_sources.real_sources.requests.get", return_value=mock_resp), \
         patch("src.data_sources.real_sources.time.sleep", side_effect=[None, StopPolling]) as mock_sleep:
        with pytest.raises(StopPolling):
            next(ws._stream())

    assert ws.status == "DEGRADED"
    # Backoff sleep was called with Retry-After value
    assert any(args[0] == 4.5 for args, _ in mock_sleep.call_args_list)

def test_weather_timeout_and_connection_error():
    ws = WeatherSource({})
    ws.cities = ws.cities[:1]
    ws.cached_observations["Chennai"] = {"temperature": 30.0, "condition": "Clear Sky"}

    with patch("src.data_sources.real_sources.requests.get", side_effect=requests.Timeout("Connection timed out")), \
         patch("src.data_sources.real_sources.time.sleep", side_effect=StopPolling):
        with pytest.raises(StopPolling):
            next(ws._stream())

    assert ws.status == "OFFLINE"
    # Valid cached data was retained
    assert ws.cached_observations["Chennai"]["temperature"] == 30.0

def test_weather_missing_values_single_city():
    ws = WeatherSource({})
    ws.cities = SOUTH_INDIA_CITIES[:2]
    ws.batch_size = 2

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = [
        {"current": {"temperature_2m": None, "weather_code": None}},  # City 1 incomplete
        {"current": {"temperature_2m": 29.0, "weather_code": 0}}     # City 2 complete
    ]

    with patch("src.data_sources.real_sources.requests.get", return_value=mock_resp), \
         patch("src.data_sources.real_sources.time.sleep", side_effect=StopPolling):
        stream = ws._stream()
        ev = next(stream)

    assert ev["data"]["city"] == "Coimbatore"
    assert ev["data"]["temperature"] == 29.0

def test_weather_cache_retention_and_recovery():
    ws = WeatherSource({})
    ws.cities = SOUTH_INDIA_CITIES[:1]

    resp_ok = MagicMock()
    resp_ok.status_code = 200
    resp_ok.headers = {}
    resp_ok.json.return_value = {"current": {"temperature_2m": 32.0, "weather_code": 0, "time": "2026-10-13T04:15"}}

    resp_fail = MagicMock()
    resp_fail.status_code = 503
    resp_fail.headers = {}

    resp_recov = MagicMock()
    resp_recov.status_code = 200
    resp_recov.headers = {}
    resp_recov.json.return_value = {"current": {"temperature_2m": 32.5, "weather_code": 1, "time": "2026-10-13T04:30"}}

    with patch("src.data_sources.real_sources.requests.get", side_effect=[resp_ok, resp_fail, resp_recov]), \
         patch("src.data_sources.real_sources.time.sleep", side_effect=[None, None, StopPolling]):
        stream = ws._stream()
        ev1 = next(stream)
        assert ws.status == "LIVE"
        assert ws.cached_observations["Chennai"]["temperature"] == 32.0

        # After failure, next item in stream recovers on 3rd attempt
        ev2 = next(stream)
        assert ws.status == "LIVE"
        assert ev2["data"]["temperature"] == 32.5
        assert ws.cached_observations["Chennai"]["temperature"] == 32.5

def test_air_quality_batched_parsing_and_anomalies():
    aq = AirQualitySource({})
    aq.cities = SOUTH_INDIA_CITIES[:2]
    aq.batch_size = 2

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = [
        {"current": {"us_aqi": 165, "pm2_5": 85.0, "pm10": 130.0, "nitrogen_dioxide": 40.0, "time": "2026-10-13T04:00"}},
        {"current": {"us_aqi": 45, "pm2_5": 12.0, "pm10": 25.0, "nitrogen_dioxide": 8.0, "time": "2026-10-13T04:00"}}
    ]

    with patch("src.data_sources.real_sources.requests.get", return_value=mock_resp), \
         patch("src.data_sources.real_sources.time.sleep", side_effect=StopPolling):
        stream = aq._stream()
        ev1 = next(stream)
        ev2 = next(stream)

    assert ev1["data"]["city"] == "Chennai"
    assert ev1["data"]["air_quality_index"] == 165
    assert ev1["data"]["severity"] == "CRITICAL"
    assert ev1["data"]["anomaly"] is True

    assert ev2["data"]["city"] == "Coimbatore"
    assert ev2["data"]["air_quality_index"] == 45
    assert ev2["data"]["severity"] == "LOW"
    assert ev2["data"]["anomaly"] is False
    assert aq.status == "LIVE"

def test_gtfs_feedmessage_decoding_and_stale_rejection():
    gtfs = GTFSTransitSource({"data_sources": {"transit": {"feed_url": "https://transit.example/gtfs-rt"}}})
    now_ts = datetime.datetime.now(datetime.timezone.utc).timestamp()

    feed_json = {
        "header": {"gtfs_realtime_version": "2.0", "timestamp": int(now_ts)},
        "entity": [
            {
                "id": "trip_101",
                "trip_update": {
                    "trip": {"trip_id": "T101", "route_id": "MRTS-1"},
                    "stop_time_update": [{"arrival": {"delay": 420}}],
                    "timestamp": int(now_ts - 60)  # Fresh (1 min old)
                }
            },
            {
                "id": "trip_stale",
                "trip_update": {
                    "trip": {"trip_id": "T_OLD", "route_id": "MRTS-OLD"},
                    "stop_time_update": [{"arrival": {"delay": 1200}}],
                    "timestamp": int(now_ts - 3600)  # Stale (1 hour old) -> must be rejected
                }
            },
            {
                "id": "veh_202",
                "vehicle": {
                    "vehicle": {"id": "BUS-42"},
                    "position": {"latitude": 13.0827, "longitude": 80.2707, "speed": 12.5},
                    "timestamp": int(now_ts - 30)  # Fresh
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.json.return_value = feed_json

    with patch("src.data_sources.real_sources.requests.get", return_value=mock_resp), \
         patch("src.data_sources.real_sources.time.sleep", side_effect=StopPolling):
        stream = gtfs._stream()
        ev1 = next(stream)
        ev2 = next(stream)

    assert ev1["data"]["event_type"] == "transit_trip_update"
    assert ev1["data"]["trip_id"] == "T101"
    assert ev1["data"]["delay_minutes"] == 7.0
    assert ev1["data"]["mode"] == "LIVE"

    assert ev2["data"]["event_type"] == "transit_vehicle_position"
    assert ev2["data"]["vehicle_id"] == "BUS-42"
    assert ev2["data"]["speed_kmh"] == 45.0

    assert gtfs.status == "LIVE"
    assert gtfs.last_updated != "N/A"

def test_gtfs_invalid_feed_handling():
    gtfs = GTFSTransitSource({"data_sources": {"transit": {"feed_url": "https://transit.example/invalid"}}})

    mock_resp = MagicMock()
    mock_resp.status_code = 502
    mock_resp.headers = {}

    with patch("src.data_sources.real_sources.requests.get", return_value=mock_resp), \
         patch("src.data_sources.real_sources.time.sleep", side_effect=StopPolling):
        with pytest.raises(StopPolling):
            next(gtfs._stream())

    assert gtfs.status == "DEGRADED"

def test_traffic_adapter_interfaces_unconfigured_truthfulness(monkeypatch):
    monkeypatch.delenv("TOMTOM_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_MAPS_TRAFFIC_API_KEY", raising=False)

    tomtom = TomTomTrafficConnector()
    assert tomtom.is_configured() is False
    assert tomtom.fetch_flow(13.0827, 80.2707) is None

    google = GoogleTrafficConnector()
    assert google.is_configured() is False
    assert google.fetch_flow(13.0827, 80.2707) is None

def test_gtfs_binary_protobuf_fixture_decoding():
    """
    Verifies that GTFSTransitSource decodes actual binary protobuf FeedMessage bytes
    from google.transit.gtfs_realtime_pb2.
    """
    from google.transit import gtfs_realtime_pb2
    now_ts = time.time()

    msg = gtfs_realtime_pb2.FeedMessage()
    msg.header.gtfs_realtime_version = "2.0"
    msg.header.timestamp = int(now_ts)

    # 1. Trip Update Entity
    ent1 = msg.entity.add()
    ent1.id = "tu-chennai-101"
    ent1.trip_update.trip.trip_id = "TRIP-CHN-EXP-01"
    ent1.trip_update.trip.route_id = "ROUTE-BLUE-LINE"
    ent1.trip_update.timestamp = int(now_ts - 20)
    stu = ent1.trip_update.stop_time_update.add()
    stu.arrival.delay = 900  # 15 minutes delay

    # 2. Vehicle Position Entity
    ent2 = msg.entity.add()
    ent2.id = "veh-chennai-502"
    ent2.vehicle.vehicle.id = "BUS-MTC-502"
    ent2.vehicle.position.latitude = 13.0827
    ent2.vehicle.position.longitude = 80.2707
    ent2.vehicle.position.speed = 10.0  # 10 m/s = 36 km/h
    ent2.vehicle.timestamp = int(now_ts - 10)

    # 3. Stale Entity (> 900s old) - Should be rejected
    ent3 = msg.entity.add()
    ent3.id = "stale-ent"
    ent3.trip_update.trip.trip_id = "TRIP-STALE"
    ent3.trip_update.timestamp = int(now_ts - 1500)

    pb_bytes = msg.SerializeToString()
    assert len(pb_bytes) > 0

    gtfs = GTFSTransitSource({"data_sources": {"transit": {"feed_url": "https://mtc.chennai.gov.in/gtfs-rt.pb"}}})

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = pb_bytes
    mock_resp.json.side_effect = ValueError("Not JSON")

    with patch("src.data_sources.real_sources.requests.get", return_value=mock_resp), \
         patch("src.data_sources.real_sources.time.sleep", side_effect=StopPolling):
        stream = gtfs._stream()
        ev1 = next(stream)
        ev2 = next(stream)

    assert ev1["data"]["event_type"] == "transit_trip_update"
    assert ev1["data"]["trip_id"] == "TRIP-CHN-EXP-01"
    assert ev1["data"]["delay_minutes"] == 15.0
    assert ev1["data"]["mode"] == "LIVE"

    assert ev2["data"]["event_type"] == "transit_vehicle_position"
    assert ev2["data"]["vehicle_id"] == "BUS-MTC-502"
    assert ev2["data"]["speed_kmh"] == 36.0

    assert gtfs.status == "LIVE"
    assert gtfs.last_updated != "N/A"
