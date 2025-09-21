import pytest
from src.processing import RAGSystem

def test_rag_system():
    config = {
        'llm': {
            'model': 'gpt-3.5-turbo',
            'api_key': 'test_key',
            'temperature': 0.3
        }
    }
    rag_system = RAGSystem(config)
    
    # Test adding document
    data = {
        "noise_level": 90,
        "crowd_density": 0.9
    }
    source = "city_sensors"
    location = {
        "lat": 40.7128,
        "lon": -74.0060
    }
    
    result = rag_system.add_document(data, source, location)
    assert result == True
    assert len(rag_system.documents) == 1
    
    # Test querying
    # Note: This would require mocking the LLM in a real test
    # response = rag_system.query("What is the noise level at Central Park?")
    # assert isinstance(response, str)
