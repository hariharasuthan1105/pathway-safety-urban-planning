import pytest
import pathway as pw
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
    assert "anomaly" not in result
    
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
