# Real-Time Urban Intelligence & AI Copilot

An end-to-end real-time urban intelligence platform and Human-in-the-Loop AI Copilot featuring Pathway-based real-time streaming with grounded RAG, optional Groq LLM integration, and deterministic fallback Copilot.

---

## Overview

The **Real-Time Urban Intelligence Platform** ingests heterogeneous city telemetry (weather, air quality, traffic sensors, police scanner alerts, and HTTP webhooks), streams and processes events through **Pathway**, maintains a real-time **Live City State**, detects temporal anomalies, computes dynamic 0–100 risk scores, correlates events across independent data sources, and provides an evidence-grounded **AI Urban Copilot**.

Operators interact with the system via a modern React/Vite dashboard and an HTTP REST API (`POST /api/ask`). The AI Urban Copilot translates natural-language queries into structured analysis, verifiable audit evidence citations, Human-in-the-Loop decision recommendations, and safe client-side dashboard focus actions.

---

## Architecture Accuracy

> **Architecture**: Pathway Streaming + Real-Time Grounded Retrieval + Optional Groq LLM + Deterministic Fallback Copilot.
>
> **LLM Provider**: Groq (optional).
> **Fallback**: Deterministic/mock Copilot when `GROQ_API_KEY` is absent.
>
> *Groq is optional. The Urban Intelligence platform remains fully operational in fallback mode without an external LLM API key.*

---

## Key Capabilities

- **Real-Time Event Streaming**: High-throughput event ingestion and transformation via Pathway streaming tables (`pw.Table`).
- **Multi-Source Urban Telemetry**: Real-time integration with Open-Meteo Weather API, Open-Meteo Air Quality API, and HTTP webhooks.
- **Webhook Event Ingestion**: Standalone HTTP server (`POST /events`) for external incident payloads.
- **Spatial Zone Intelligence**: Spatial bucketing mapping latitude/longitude coordinates into geographic zones.
- **Rolling Time-Window Analysis**: Sliding aggregations (5m, 15m, 30m, 60m) measuring event velocity and rate-of-change acceleration ratios.
- **Dynamic City Risk Scoring**: Transparent deterministic 0–100 risk score with risk levels (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) and factor breakdowns.
- **Temporal Anomaly Detection**: Detects frequency acceleration surges (> 2.0x baseline) and critical incident bursts.
- **Cross-Source Event Correlation**: Identifies multi-source incident overlaps (e.g., weather + traffic + webhook collision) in short time windows.
- **Evidence-Grounded RAG**: Dynamically formats up-to-the-second Live City State telemetry into prompt context without manual vector index rebuilds.
- **Groq-Powered AI Copilot (Optional)**: Grounded query synthesis via official Groq API (`llama-3.3-70b-versatile`) with fallback parsing and timeout safety.
- **Deterministic Intent Routing**: Classifies queries into explainable intents (`CITY_SUMMARY`, `RISK_EXPLANATION`, `ZONE_ANALYSIS`, `EVENT_INVESTIGATION`, `EVENT_COMPARISON`, `TIME_WINDOW_ANALYSIS`, `SOURCE_ANALYSIS`, `EVIDENCE_LOOKUP`).
- **Human-in-the-Loop Recommendations**: All AI suggestions are explicitly labeled `[HUMAN REVIEW RECOMMENDATION]`. No autonomous emergency service dispatch or traffic alteration claims.
- **Multimodal Data Modes**: Configurable via environment variables (`live`, `hybrid`, `simulation`).

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Streaming Pipeline** | Pathway |
| **Backend** | Python 3.10+ (FastAPI / Uvicorn) |
| **LLM Provider** | Groq API (`llama-3.3-70b-versatile`, optional) / Deterministic Fallback Copilot |
| **RAG** | Real-time grounded context assembler |
| **Frontend** | React, Vite, Tailwind CSS, Lucide Icons |
| **Data Sources** | Open-Meteo REST API, Air Quality API, HTTP Webhooks, Simulated Traffic Stream |
| **Analytics** | Rolling sliding windows, Anomaly detection UDFs, Risk scoring engine |
| **Testing** | Pytest (39 passing tests) |
| **Configuration** | Environment variables (`python-dotenv`, PyYAML) |

---

## Real-Time Pipeline

Incoming events flow through the system in a continuous streaming sequence:

$$\text{Event} \longrightarrow \text{Pathway Processing} \longrightarrow \text{City State Update} \longrightarrow \text{Risk Recalculation} \longrightarrow \text{Anomaly / Correlation Analysis} \longrightarrow \text{RAG Context} \longrightarrow \text{Copilot Response} \longrightarrow \text{Dashboard}$$

1. **Ingestion & Normalization**: Data source connectors wrap raw payloads into unified `CityEvent` schemas.
2. **Pathway Graph Execution**: Pathway streaming tables (`pw.Table`) concatenate feeds and evaluate UDFs (`AnomalyDetector.process`) in parallel.
3. **State Aggregation**: `CityStateManager` computes sliding 5m–60m window metrics, spatial zone counts, deterministic risk scores (0–100), and cross-source correlations.
4. **Context Update**: `RAGSystem` formats the latest Live City State and recent event history into structured prompt context.
5. **Copilot Response & UI Rendering**: The AI Urban Copilot generates evidence-grounded analysis, advisory review recommendations, and dashboard focus actions for operator review.

---

## Environment Setup

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
DATA_MODE=hybrid
SYSTEM_MODE=public_safety
LOCATION_LAT=13.0827
LOCATION_LON=80.2707

# Optional Groq LLM integration (Runs in deterministic fallback mode if key is absent):
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.2
```

*(Note: Groq is optional. The Urban Intelligence platform remains fully operational in fallback mode without an external LLM API key).*

---

## API & Webhooks

The platform exposes HTTP endpoints on port `8000`:

### 1. Ingest Webhook Incident Payload (`POST /events`)
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "vehicle_collision",
    "severity": "CRITICAL",
    "latitude": 13.0827,
    "longitude": 80.2707,
    "source": "police_scanner",
    "data": {
      "description": "3-vehicle collision blocking two lanes"
    }
  }'
```

### 2. Query AI Urban Copilot (`POST /api/ask`)
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the safety and traffic status in Chennai right now?"
  }'
```

---

## Testing

Run the full automated test suite offline:
```bash
pytest -v
```

### Current Test Result:
```text
======================== 39 passed, 1 warning in 6.37s ========================
```

- All 39 unit tests execute offline in under 7 seconds.
- Unit tests use `MockLLMProvider` or mocked Groq responses and do not make live external API calls.

---

## Security

- **Backend-Only API Keys**: `GROQ_API_KEY` is strictly evaluated on the backend server.
- **Zero Frontend Exposure**: No API keys are exposed to Vite or client-side JavaScript.
- **Git Safety**: `.env` is explicitly included in `.gitignore` and is never committed to source control.
- **Template Security**: `.env.example` contains placeholder values only.
- **Zero Committed Credentials**: No real API keys exist in tracked files.

