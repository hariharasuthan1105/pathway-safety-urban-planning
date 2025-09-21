import pytest
from src.data_sources import SocialMediaSource, PublicSafetySource, IoTSensorSource

def test_social_media_source():
    config = {
        'mode': 'public_safety',
        'data_sources': {
            'social_media': {
                'enabled': True,
                'keywords': ["fire", "accident", "protest", "emergency"]
            }
        }
    }
    source = SocialMediaSource(config)
    assert source.name == "social_media"
    
    schema = source._define_schema()
    assert 'timestamp' in schema
    assert 'source' in schema
    assert 'data' in schema
    assert 'location' in schema

def test_public_safety_source():
    config = {
        'mode': 'public_safety',
        'data_sources': {
            'public_safety': {
                'enabled': True
            }
        }
    }
    source = PublicSafetySource(config)
    assert source.name == "public_safety"
    
    schema = source._define_schema()
    assert 'timestamp' in schema
    assert 'source' in schema
    assert 'data' in schema
    assert 'location' in schema

def test_iot_sensor_source():
    config = {
        'mode': 'public_safety',
        'data_sources': {
            'iot_sensors': {
                'enabled': True,
                'simulation_rate': 0.5
            }
        }
    }
    source = IoTSensorSource(config)
    assert source.name == "iot_sensors"
    
    schema = source._define_schema()
    assert 'timestamp' in schema
    assert 'source' in schema
    assert 'data' in schema
    assert 'location' in schema
