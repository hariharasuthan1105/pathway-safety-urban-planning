import pytest
from src.processing import RAGSystem

def test_rag_system():
    config = {
        'llm': {
            'model': 'llama-3.3-70b-versatile',
            'api_key': 'YOUR_GROQ_API_KEY',
            'temperature': 0.2
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
    
    # Test querying without API key returns informative string
    response = rag_system.query("What is the noise level at Central Park?")
    assert isinstance(response, str)
    assert "Based on retrieved live telemetry" in response or "RAG System" in response



