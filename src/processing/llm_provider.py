"""
Isolated LLM Provider Layer for Phase 5.

Supports OpenAI API integration with structured prompt execution,
fallback parsing, timeout safety, and mock provider support for testing.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class BaseLLMProvider:
    """Abstract base class for LLM providers."""
    def is_configured(self) -> bool:
        raise NotImplementedError

    def generate_structured_response(self, prompt: str, system_instruction: str = "") -> Dict[str, Any]:
        raise NotImplementedError

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API implementation with structured JSON extraction."""
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo", temperature: float = 0.2):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        self.model = model
        self.temperature = temperature

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "YOUR_OPENAI_API_KEY")

    def generate_structured_response(self, prompt: str, system_instruction: str = "") -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "error": "MISSING_API_KEY",
                "answer": "AI LLM is not configured. Live city intelligence and RAG are available, but natural-language synthesis requires an LLM API key.",
                "risk_level": "UNKNOWN",
                "confidence": "NONE",
                "affected_zones": [],
                "key_factors": [],
                "evidence": []
            }

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=800
            )

            raw_text = response.choices[0].message.content or ""
            return self._parse_json_response(raw_text)

        except Exception as e:
            logger.error(f"[OpenAIProvider] Error generating response: {e}")
            return {
                "error": str(e),
                "answer": f"Error communicating with LLM provider: {str(e)}",
                "risk_level": "UNKNOWN",
                "confidence": "LOW",
                "affected_zones": [],
                "key_factors": ["LLM service request failed"],
                "evidence": []
            }

    def _parse_json_response(self, raw_text: str) -> Dict[str, Any]:
        """Strips markdown block markers and parses JSON cleanly."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return {
                    "answer": parsed.get("answer", raw_text),
                    "risk_level": parsed.get("risk_level", "MODERATE"),
                    "confidence": parsed.get("confidence", "HIGH"),
                    "affected_zones": parsed.get("affected_zones", []),
                    "key_factors": parsed.get("key_factors", []),
                    "evidence": parsed.get("evidence", [])
                }
        except Exception:
            logger.warning("[OpenAIProvider] Failed to parse JSON response. Falling back to plain text answer.")

        return {
            "answer": raw_text,
            "risk_level": "MODERATE",
            "confidence": "MEDIUM",
            "affected_zones": [],
            "key_factors": [],
            "evidence": []
        }

class MockLLMProvider(BaseLLMProvider):
    """Deterministic Mock LLM Provider for unit testing and offline validation."""
    def __init__(self, mock_answer: Optional[str] = None):
        self.mock_answer = mock_answer

    def is_configured(self) -> bool:
        return True

    def generate_structured_response(self, prompt: str, system_instruction: str = "") -> Dict[str, Any]:
        return {
            "answer": self.mock_answer or "Based on retrieved live telemetry, Zone A (Downtown) is at HIGH risk due to a critical traffic collision corroborated by weather data.",
            "risk_level": "HIGH",
            "confidence": "HIGH",
            "affected_zones": ["Zone A (Downtown)"],
            "key_factors": [
                "1 critical vehicle collision reported via webhook",
                "Gridlock traffic detected on traffic API",
                "Cross-source corroboration across 3 independent sources"
            ],
            "evidence": [
                {
                    "event_id": "demo_wh01",
                    "source": "webhook_ingestion",
                    "timestamp": "2026-10-05T15:00:00Z",
                    "zone": "Zone A (Downtown)",
                    "severity": "CRITICAL"
                }
            ]
        }
