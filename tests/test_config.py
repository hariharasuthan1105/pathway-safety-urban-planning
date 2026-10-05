import os
import pytest
from src.main import load_config
from src.processing import RAGSystem

def test_valid_configuration_loading(tmp_path):
    config_file = tmp_path / "valid_config.yaml"
    config_content = """
mode: public_safety
data_sources:
  social_media:
    enabled: true
llm:
  model: "gpt-3.5-turbo"
  api_key: "test_key"
"""
    config_file.write_text(config_content)
    
    config = load_config(str(config_file))
    assert config['mode'] == 'public_safety'
    assert config['data_sources']['social_media']['enabled'] is True

def test_missing_required_secret_warning(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = {
        'llm': {
            'model': 'gpt-3.5-turbo',
            'api_key': 'YOUR_OPENAI_API_KEY'
        }
    }
    rag = RAGSystem(config)
    assert rag.has_valid_key is False
    rag.add_document({"noise_level": 90}, "sensor_1", {"lat": 40.7, "lon": -74.0})
    query_result = rag.query("Test question")
    assert "OPENAI_API_KEY" in query_result or "LLM Key Missing" in query_result

