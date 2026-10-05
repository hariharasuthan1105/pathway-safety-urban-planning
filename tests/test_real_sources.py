import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.models import create_city_event
from src.data_sources.real_sources import WeatherSource, AirQualitySource, GTFSTransitSource, WebhookSource, ingest_webhook_payload

def test_city_event_creation():
    event = create_city_event(
        source="weather_api",
        event_type="weather_update",
        latitude=40.7128,
        longitude=-74.0060,
        severity="LOW",
        data={"temperature": 22.5}
    )
    assert event["source"] == "weather_api"
    assert event["data"]["event_type"] == "weather_update"
    assert event["data"]["temperature"] == 22.5
    assert event["location"]["lat"] == 40.7128
    assert event["location"]["lon"] == -74.0060
    assert "timestamp" in event
    assert "event_id" in event["data"]

@patch("requests.get")
def test_weather_source_parsing(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "current_weather": {
            "temperature": 28.5,
            "windspeed": 14.2,
            "weathercode": 0
        }
    }
    mock_get.return_value = mock_resp

    config = {'location': {'lat': 40.7128, 'lon': -74.0060}}
    ws = WeatherSource(config)
    stream = ws._stream()
    event = next(stream)

    assert event["source"] == "weather_api"
    assert event["data"]["temperature"] == 28.5
    assert event["data"]["condition"] == "Clear Sky"
    assert ws.status == "LIVE"

@patch("requests.get")
def test_air_quality_source_anomaly(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "current": {
            "us_aqi": 140,
            "pm2_5": 45.0,
            "pm10": 80.0,
            "nitrogen_dioxide": 25.0
        }
    }
    mock_get.return_value = mock_resp

    config = {'location': {'lat': 40.7128, 'lon': -74.0060}}
    aq = AirQualitySource(config)
    stream = aq._stream()
    event = next(stream)

    assert event["source"] == "air_quality_api"
    assert event["data"]["air_quality_index"] == 140
    assert event["data"]["severity"] == "HIGH"
    assert event["data"]["anomaly"] is True
    assert aq.status == "LIVE"

def test_gtfs_transit_unconfigured():
    config = {'data_sources': {'transit': {'enabled': True}}}
    gtfs = GTFSTransitSource(config)
    assert gtfs.status == "NOT CONFIGURED"
    
    stream = gtfs._stream()
    event = next(stream)
    assert event["source"] == "gtfs_transit_api"
    assert event["data"]["status"] == "NOT CONFIGURED"

def test_webhook_ingestion():
    payload = {
        "event_type": "accident",
        "severity": "CRITICAL",
        "latitude": 40.7589,
        "longitude": -73.9851,
        "source": "police_dispatch",
        "data": {"description": "Traffic collision at Times Square"}
    }
    event = ingest_webhook_payload(payload)
    assert event["source"] == "police_dispatch"
    assert event["data"]["event_type"] == "accident"
    assert event["data"]["severity"] == "CRITICAL"
    assert event["location"]["lat"] == 40.7589
    assert event["location"]["lon"] == -73.9851
