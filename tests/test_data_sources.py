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
    assert hasattr(schema, 'timestamp') or 'timestamp' in getattr(schema, '__annotations__', {})

    # Test event generation
    stream = source._stream()
    event = next(stream)
    assert 'timestamp' in event
    assert event['source'] == 'twitter'
    assert 'data' in event
    assert 'location' in event

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
    assert hasattr(schema, 'timestamp') or 'timestamp' in getattr(schema, '__annotations__', {})

    # Test event generation
    stream = source._stream()
    event = next(stream)
    assert 'timestamp' in event
    assert event['source'] == 'police_scanner'
    assert 'data' in event

def test_iot_sensor_source():
    config = {
        'mode': 'public_safety',
        'data_sources': {
            'iot_sensors': {
                'enabled': True,
                'simulation_rate': 0.01
            }
        }
    }
    source = IoTSensorSource(config)
    assert source.name == "iot_sensors"
    
    schema = source._define_schema()
    assert hasattr(schema, 'timestamp') or 'timestamp' in getattr(schema, '__annotations__', {})

    # Test event generation
    stream = source._stream()
    event = next(stream)
    assert 'timestamp' in event
    assert event['source'] == 'city_sensors'
    assert 'noise_level' in event['data']
