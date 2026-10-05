import pytest

from src.pathway_compat import pw

from src.processing import AnomalyDetector

def test_anomaly_detector():
    config = {
        'anomaly_rules': {
            'noise_level': 80,
            'crowd_density': 0.8,
            'social_media_spike': 10,
            'traffic_flow': 0.2
        }
    }
    detector = AnomalyDetector(config)
    
    # Test normal data
    normal_data = {
        "source": "city_sensors",
        "data": {
            "noise_level": 60,
            "crowd_density": 0.5,
            "traffic_flow": 0.6
        },
        "location": {
            "lat": 40.7128,
            "lon": -74.0060
        }
    }
    
    result = detector.process(normal_data)
    assert result.get("anomaly", False) == False
    
    # Test anomalous data
    anomalous_data = {
        "source": "city_sensors",
        "data": {
            "noise_level": 90,
            "crowd_density": 0.5,
            "traffic_flow": 0.6
        },
        "location": {
            "lat": 40.7128,
            "lon": -74.0060
        }
    }
    
    result = detector.process(anomalous_data)
    assert result["anomaly"] == True
    assert result["anomaly_type"] == "noise_level_anomaly"


def test_pathway_anomaly_detector_udf_execution():
    """
    Regression test ensuring Pathway UDF execution of AnomalyDetector.process
    works cleanly inside pw.run() streaming pipeline without missing positional argument errors.
    """
    from src.data_sources.base import GeneratorConnectorSubject

    config = {
        'anomaly_rules': {
            'noise_level': 80
        }
    }
    detector = AnomalyDetector(config)

    def test_generator():
        yield {
            "timestamp": "2026-10-05T22:00:00Z",
            "source": "city_sensors",
            "data": {"noise_level": 95},
            "location": {"lat": 13.08, "lon": 80.27}
        }

    class EventSchema(pw.Schema):
        timestamp: str
        source: str
        data: pw.Json
        location: pw.Json

    subject = GeneratorConnectorSubject(test_generator)
    stream = pw.io.python.read(subject, schema=EventSchema)

    processed = stream.select(
        source=stream.source,
        data=detector.process(stream.data),
        location=stream.location
    )

    output_events = []
    def sink(row):
        output_events.append(row)

    if hasattr(processed, "subscribe"):
        processed.subscribe(sink)
    elif hasattr(pw.io, "subscribe"):
        pw.io.subscribe(processed, sink)

    try:
        pw.run()
        import time
        time.sleep(0.5)
        assert len(output_events) > 0
        assert output_events[0]["data"].get("anomaly") == True
        assert output_events[0]["data"].get("anomaly_type") == "noise_level_anomaly"
    finally:
        if hasattr(pw, "_active_streams"):
            pw._active_streams.clear()



