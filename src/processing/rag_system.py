"""
Pathway Real-Time RAG System & LLM Integration for Phase 5.

Maintains real-time document indexing, retrieves streaming City State context,
constructs grounded prompt schemas, and delegates natural language synthesis to
the LLM provider layer.
"""

import os
import json
import datetime
import logging
from typing import Dict, Any, List, Optional

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

from .llm_provider import BaseLLMProvider, OpenAIProvider, MockLLMProvider
from .copilot_engine import CopilotEngine

logger = logging.getLogger(__name__)

SYSTEM_GROUNDED_INSTRUCTION = """You are the AI Urban Intelligence Assistant for a real-time public safety and urban planning command center.
Your task is to answer user queries using ONLY the provided live city state telemetry, active anomalies, evidence records, and cross-source correlations.

STRICT OPERATIONAL DIRECTIVES:
1. Base all statements STRICTLY on supplied evidence. Do NOT invent incidents, metrics, or statistics.
2. If evidence is insufficient to answer the query, state explicitly: "Insufficient real-time evidence available."
3. Distinguish observed empirical facts from potential analytical interpretations.
4. Do NOT claim autonomous executive authority or issue real-world emergency dispatch orders.
5. ALWAYS respond with a structured JSON object containing the exact keys:
   - "answer": (string) Clear, professional natural language response.
   - "risk_level": (string) One of ["LOW", "MODERATE", "HIGH", "CRITICAL"].
   - "confidence": (string) One of ["LOW", "MEDIUM", "HIGH"].
   - "affected_zones": (list of strings) Names of affected geographic zones.
   - "key_factors": (list of strings) Key contributing risk factors.
   - "evidence": (list of objects) Objects containing {"event_id", "source", "timestamp", "zone", "severity"}.
"""

class RAGSystem:
    def __init__(self, config: Dict[str, Any], provider: Optional[BaseLLMProvider] = None):
        self.config = config or {}
        llm_config = self.config.get('llm', {})
        
        self.api_key = os.getenv('OPENAI_API_KEY') or llm_config.get('api_key', '')
        if not self.api_key or self.api_key == "YOUR_OPENAI_API_KEY":
            logger.warning("OPENAI_API_KEY is missing or set to placeholder. RAG system running in key-missing status mode.")
            self.has_valid_key = False
        else:
            self.has_valid_key = True

        self.model_name = llm_config.get('model', 'gpt-3.5-turbo')
        self.temperature = llm_config.get('temperature', 0.2)

        # Provider & Copilot Engine injection
        self.provider = provider or OpenAIProvider(
            api_key=self.api_key,
            model=self.model_name,
            temperature=self.temperature
        )
        self.copilot_engine = CopilotEngine(self.config)
        self.documents: List[Dict[str, Any]] = []

    @pw.udf
    def add_document(self, data: Dict[str, Any], source: str, location: Dict[str, Any]) -> bool:
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc = {
            "timestamp": timestamp_str,
            "source": source,
            "data": data if isinstance(data, dict) else {},
            "location": location if isinstance(location, dict) else {}
        }
        self.documents.append(doc)
        logger.debug(f"Document added to RAG index from source {source}")
        return True

    def prepare_city_state_context(self, city_state: Dict[str, Any]) -> str:
        """
        Prepares structured live city state context for retrieval by Phase 5 Pathway LLM / RAG.
        """
        if not city_state:
            return "No active City State recorded."

        risk_score = city_state.get("overall_risk_score", 0)
        risk_level = city_state.get("overall_risk_level", "LOW")
        risk_trend = city_state.get("risk_trend", "STABLE")
        factors = city_state.get("contributing_factors", [])
        evidence = city_state.get("evidence", [])
        anomalies = city_state.get("active_anomalies", [])
        correlations = city_state.get("correlations", [])
        zone_summaries = city_state.get("zone_summaries", {})

        context_lines = [
            f"=== LIVE CITY STATE SUMMARY ===",
            f"Overall Risk Index: {risk_score}/100 ({risk_level}) | Risk Trend: {risk_trend}",
            f"Main Contributing Factors: {', '.join(factors) if factors else 'None'}",
            f"\n--- AUDIT EVIDENCE TRAIL ---"
        ]
        context_lines.extend([f"- {ev}" for ev in evidence])

        if zone_summaries:
            context_lines.append("\n--- GEOGRAPHIC ZONE BREAKDOWN ---")
            for z_name, z_info in zone_summaries.items():
                if z_info.get("event_count", 0) > 0:
                    context_lines.append(
                        f"- {z_name}: Risk Score={z_info.get('risk_score')}/100 ({z_info.get('risk_level')}), "
                        f"Events={z_info.get('event_count')} (Critical={z_info.get('critical_count')}, High={z_info.get('high_count')})"
                    )

        if anomalies:
            context_lines.append("\n--- ACTIVE OPERATIONAL ANOMALIES ---")
            for an in anomalies:
                context_lines.append(f"- [{an.get('severity', 'HIGH')}] {an.get('anomaly_type')}: {an.get('description')} (Zone: {an.get('zone')})")

        if correlations:
            context_lines.append("\n--- CROSS-SOURCE CORRELATIONS ---")
            for c in correlations:
                context_lines.append(f"- [{c.get('risk_level')}] {c.get('reason')} | Sources: {', '.join(c.get('sources', []))}")

        return "\n".join(context_lines)

    def query_structured(self, question: str, city_state: Optional[Dict[str, Any]] = None, k: int = 5) -> Dict[str, Any]:
        """
        Executes real-time RAG context retrieval and queries the LLM provider for a structured response.
        """
        if not question or not question.strip():
            return {
                "error": "EMPTY_QUESTION",
                "answer": "Please enter a valid query about real-time urban telemetry.",
                "risk_level": "LOW",
                "confidence": "HIGH",
                "affected_zones": [],
                "key_factors": [],
                "evidence": []
            }

        # Check if LLM provider is configured
        if not self.provider.is_configured():
            docs_str = ""
            if self.documents:
                relevant_docs = self.documents[-k:]
                docs_str = "\n".join([f"Source: {doc.get('source')}, Data: {doc.get('data')}" for doc in relevant_docs])

            ans_text = (
                f"[RAG System Notice] OPENAI_API_KEY is missing or set to placeholder in .env.\n"
                f"Live city intelligence and Pathway RAG context extraction are active (Retrieved {len(self.documents)} events).\n"
                f"{docs_str}\n"
                f"Set OPENAI_API_KEY to enable full LLM natural language synthesis."
            )

            return {
                "error": "MISSING_API_KEY",
                "answer": ans_text,
                "risk_level": city_state.get("overall_risk_level", "UNKNOWN") if city_state else "UNKNOWN",
                "confidence": "NONE",
                "affected_zones": [z for z, info in (city_state.get("zone_summaries", {}).items() if city_state else []) if info.get("event_count", 0) > 0],
                "key_factors": city_state.get("contributing_factors", []) if city_state else [],
                "evidence": []
            }

        # Build Context from CityState + Recent Documents
        city_state_str = self.prepare_city_state_context(city_state) if city_state else "No city state supplied."
        
        relevant_docs = self.documents[-k:] if self.documents else []
        docs_str = "\n".join([
            f"- Event ID: {doc.get('data', {}).get('event_id', 'unk')} | Source: {doc.get('source')} | Zone: {doc.get('location', {}).get('zone', 'unk')} | Severity: {doc.get('data', {}).get('severity', 'LOW')} | Data: {json.dumps(doc.get('data', {}))}"
            for doc in relevant_docs
        ])

        prompt = f"""
retrieved Real-Time City State & Telemetry Context:
{city_state_str}

RETRIEVED RECENT STREAMING EVENTS:
{docs_str if docs_str else 'No individual document events in window.'}

USER QUESTION:
{question}

Provide your structured JSON response strictly adhering to the JSON schema.
"""

        response_dict = self.provider.generate_structured_response(
            prompt=prompt,
            system_instruction=SYSTEM_GROUNDED_INSTRUCTION
        )

        # Attach real evidence citations if empty
        if not response_dict.get("evidence") and relevant_docs:
            citations = []
            for doc in relevant_docs:
                d_data = doc.get("data", {}) if isinstance(doc.get("data"), dict) else {}
                citations.append({
                    "event_id": d_data.get("event_id", "evt_unk"),
                    "source": doc.get("source", "unknown"),
                    "timestamp": doc.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat()),
                    "zone": doc.get("location", {}).get("zone", "Zone A (Downtown)"),
                    "severity": d_data.get("severity", "LOW")
                })
            response_dict["evidence"] = citations[:5]

        # Enrich response via CopilotEngine (intents, Human-in-the-Loop recommendations, dashboard actions)
        return self.copilot_engine.process_copilot_request(
            question=question,
            city_state=city_state or {},
            raw_llm_response=response_dict
        )

    def query(self, question: str, k: int = 5) -> str:
        """Backward-compatibility text query wrapper."""
        res = self.query_structured(question=question, city_state=None, k=k)
        return res.get("answer", "No response generated.")
