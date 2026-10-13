import secrets
from unittest.mock import patch
import pytest
from src.processing.llm_provider import GroqProvider
from src.processing.rag_system import RAGSystem


@pytest.mark.parametrize('failure', [TimeoutError, ConnectionError, RuntimeError])
def test_provider_failure_never_discloses_secret(failure, caplog):
    sentinel = secrets.token_hex(24)
    provider = GroqProvider(api_key=sentinel)
    with patch('groq.Groq', side_effect=failure(sentinel)):
        result = provider.generate_structured_response('Current observations?')
    assert result['error'] == 'PROVIDER_UNAVAILABLE'
    assert sentinel not in str(result) + caplog.text


@pytest.mark.parametrize('output', ['not JSON', '{}', '[]', '{"answer":42}', '{"answer":"x","risk_level":"INVENTED"}'])
def test_malformed_model_output_selects_deterministic_fallback(output):
    provider = GroqProvider(api_key=secrets.token_hex(24))
    with patch.object(provider, 'generate_structured_response', return_value=provider._parse_json_response(output)):
        result = RAGSystem({}, provider=provider).query_structured('Current risk?', {})
    assert result['provider'] == 'deterministic_fallback'
