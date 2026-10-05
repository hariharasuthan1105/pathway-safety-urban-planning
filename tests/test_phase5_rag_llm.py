import pytest
import datetime
from unittest.mock import patch, MagicMock
from src.processing import CityStateManager, RAGSystem
from src.processing.llm_provider import MockLLMProvider, GroqProvider, OpenAIProvider

def test_groq_provider_selection_when_key_present(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")
    rag = RAGSystem(config={})
    assert isinstance(rag.provider, GroqProvider)
    assert rag.has_valid_key is True

def test_fallback_provider_selection_when_key_missing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    rag = RAGSystem(config={})
    assert isinstance(rag.provider, MockLLMProvider)
    assert rag.has_valid_key is False

def test_missing_api_key_handling():
    provider = GroqProvider(api_key="")
    assert not provider.is_configured()

    res = provider.generate_structured_response("What is happening right now?")
    assert res["error"] == "MISSING_API_KEY"
    assert "Groq API key not configured" in res["answer"]
    assert "api_key" not in res
    assert "gsk_" not in str(res)

def test_groq_api_failure_graceful_handling(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")
    provider = GroqProvider(api_key="gsk_test_key_12345")
    
    with patch("groq.Groq") as mock_groq:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_exception = Exception("Groq API connection timeout")
        mock_client.chat.completions.create.side_effect = Exception("Groq API connection timeout")
        mock_groq.return_value = mock_client

        res = provider.generate_structured_response("Why is risk high?")
        assert "error" in res
        assert "Groq service request failed" in res["key_factors"] or "Groq API connection timeout" in res["answer"]
        assert "gsk_test_key_12345" not in str(res)

def test_groq_mocked_success_response(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")
    provider = GroqProvider(api_key="gsk_test_key_12345")

    mock_json_response = '```json\n{"answer": "Traffic peak in Zone B.", "risk_level": "MODERATE", "confidence": "HIGH", "affected_zones": ["Zone B (Midtown)"], "key_factors": ["High traffic volume"], "evidence": []}\n```'

    with patch("groq.Groq") as mock_groq:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = mock_json_response
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        res = provider.generate_structured_response("Analyze traffic in Zone B")
        assert res["answer"] == "Traffic peak in Zone B."
        assert res["risk_level"] == "MODERATE"
        assert res["affected_zones"] == ["Zone B (Midtown)"]

def test_rag_system_context_formatting():
    csm = CityStateManager()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    ev = {
        "timestamp": now_str,
        "source": "open_meteo_weather",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "data": {"event_id": "e_rag_1", "event_type": "heavy_rain", "severity": "HIGH"}
    }
    csm.ingest_event(ev)
    live_state = csm.get_live_city_state()

    mock_provider = MockLLMProvider()
    rag = RAGSystem(config={}, provider=mock_provider)
    rag.add_document(ev["data"], ev["source"], ev["location"])

    context_str = rag.prepare_city_state_context(live_state)
    assert "LIVE CITY STATE SUMMARY" in context_str
    assert "AUDIT EVIDENCE TRAIL" in context_str
    assert "Zone A (Downtown)" in context_str

def test_rag_structured_query_with_mock_provider():
    csm = CityStateManager()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    ev = {
        "timestamp": now_str,
        "source": "webhook_ingestion",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "data": {"event_id": "wh_test_1", "event_type": "fire_alarm", "severity": "CRITICAL"}
    }
    csm.ingest_event(ev)
    live_state = csm.get_live_city_state()

    mock_provider = MockLLMProvider(mock_answer="Fire alarm reported in Zone A.")
    rag = RAGSystem(config={}, provider=mock_provider)
    rag.add_document(ev["data"], ev["source"], ev["location"])

    res = rag.query_structured("Why is Zone A high risk?", city_state=live_state)

    assert res["risk_level"] == "HIGH"
    assert "affected_zones" in res
    assert "key_factors" in res
    assert len(res["evidence"]) >= 1
    assert res["evidence"][0]["event_id"] in ["wh_test_1", "demo_wh01"]

def test_empty_question_handling():
    mock_provider = MockLLMProvider()
    rag = RAGSystem(config={}, provider=mock_provider)
    
    res = rag.query_structured("   ")
    assert res["error"] == "EMPTY_QUESTION"
    assert "valid query" in res["answer"]

def test_groq_provider_fallback_parsing():
    provider = GroqProvider(api_key="mock_key_for_unit_test")
    
    # Raw non-JSON text fallback
    raw_text = "The city is operating normally with no active incidents."
    parsed = provider._parse_json_response(raw_text)
    assert parsed["answer"] == raw_text
    assert parsed["confidence"] in ["MEDIUM", "HIGH"]

    # Markdown json block parsing
    markdown_json = '```json\n{"answer": "High traffic detected.", "risk_level": "HIGH", "confidence": "HIGH", "affected_zones": ["Zone B"], "key_factors": ["Congestion"], "evidence": []}\n```'
    parsed_json = provider._parse_json_response(markdown_json)
    assert parsed_json["answer"] == "High traffic detected."
    assert parsed_json["risk_level"] == "HIGH"
    assert parsed_json["affected_zones"] == ["Zone B"]

