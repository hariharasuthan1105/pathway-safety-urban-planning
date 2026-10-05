# REAL-TIME URBAN INTELLIGENCE PLATFORM — SYSTEM ARCHITECTURE

## System Overview & Technical Declaration

The Real-Time Urban Intelligence Platform provides a high-throughput, low-latency intelligence layer for urban safety and emergency management operations.

> **Architecture Declaration**: Pathway is used as the streaming data-processing engine. The current RAG implementation is a custom real-time grounded context layer, and LLM inference is provided through the OpenAI SDK.

---

## 1. High-Level Data Flow

```
REAL & SIMULATED DATA SOURCES (Open-Meteo Weather, Open-Meteo Air Quality, Webhooks, Simulators)
        ↓
CityEvent NORMALIZATION (Unified Event Schema)
        ↓
PATHWAY STREAMING PIPELINE (pw.Table.concat, pw.Table.select, AnomalyDetector UDF)
        ↓
REAL-TIME INTELLIGENCE ENGINE (Rolling Window Aggregations, Zone Intelligence, Risk Engine, Cross-Source Correlator)
        ↓
LIVE CITY STATE (City Risk 0-100, Evidence Trail, Zone Risk Summaries, Active Anomalies, Correlations)
        ↓
REAL-TIME GROUNDED RAG (Context Assembler: CityState + Recent Document Window)
        ↓
OPENAI LLM (OpenAIProvider / Direct SDK integration)
        ↓
AI URBAN COPILOT ENGINE (Intent Classification, Human Review Recommendations, Dashboard Action Binding)
        ↓
STREAMLIT COMMAND CENTER DASHBOARD & POST /api/ask HTTP API
```

---

## 2. Core Architectural Components

### 1. Data Ingestion & Connectors
- **Live Connectors**: Reads real-time Open-Meteo weather (temperature, precipitation, wind speed) and air quality (AQI, PM2.5, PM10) APIs.
- **Webhook Server**: Standalone HTTP server (`src/webhook_server.py`) exposing `POST /events` for external incident payload ingestion.
- **Data Modes**: Configurable via `DATA_MODE`:
  - `LIVE`: Queries external APIs and HTTP webhooks.
  - `SIMULATION`: Generates synthetic telemetry streams for offline demonstration.
  - `HYBRID`: Prioritizes live sources with automatic simulation fallback.

### 2. CityEvent Normalization
All incoming telemetry payloads are normalized into a unified dictionary structure:
```json
{
  "timestamp": "2026-10-05T16:00:00Z",
  "source": "open_meteo_weather",
  "mode": "LIVE",
  "location": {
    "lat": 40.7128,
    "lon": -74.0060,
    "zone": "Zone A (Downtown)"
  },
  "data": {
    "event_id": "evt_9a8f2c",
    "event_type": "heavy_rain",
    "severity": "HIGH",
    "anomaly": false
  }
}
```

### 3. Pathway Streaming Pipeline
- Built using `pathway` streaming tables (`pw.Table`).
- Evaluates rule-based anomaly detection UDFs (`AnomalyDetector.process`) over incoming data streams in parallel.
- Generates real-time anomaly output sinks (`anomalies.csv` and `processed_data.json`).

### 4. Real-Time Intelligence Engine
- **Rolling Windows** (`RollingWindowAggregator`): Maintains 5m, 15m, 30m, and 60m sliding windows measuring event rates and acceleration ratios.
- **Zone Intelligence** (`ZoneManager`): Spatial bucketing mapping latitude/longitude coordinates into geographic zones (Zone A Downtown, Zone B Midtown, Zone C Uptown, Zone D Outer District).
- **Risk Scoring Engine** (`RiskScoringEngine`): Transparent deterministic score (0–100) combining base severity points, recency multipliers, spatial density bonuses, source diversity bonuses, acceleration bonuses, and anomaly penalties.
- **Temporal Anomaly Detection** (`AnomalyDetector`): Flags rate acceleration spikes (> 2.0x baseline) and critical incident bursts.
- **Cross-Source Correlation** (`CrossSourceCorrelator`): Identifies multi-source overlaps (e.g. weather + traffic + emergency webhook) in the same zone and sliding time window.
- **Evidence Generation**: Preserves an audit trail explaining every risk score and anomaly.

### 5. Live City State
Unified state container (`CityStateManager`) holding:
- Overall risk score, risk level (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`), and risk trend (`INCREASING`, `STABLE`, `DECREASING`).
- Audit evidence trail and main contributing factors.
- Geographic zone summaries.
- Active operational anomalies & cross-source correlations.
- Data source freshness tracking (`LIVE`, `SIMULATION`, `HYBRID`, `STALE`, `OFFLINE`).

### 6. Real-Time Grounded RAG
- `RAGSystem` continuously indexes streaming events from Pathway.
- Dynamically formats the **Live City State** and recent document history into grounded context (`prepare_city_state_context`).
- Does NOT require rebuilding vector indexes batch-style.

### 7. OpenAI LLM Integration
- `OpenAIProvider` connects directly via the official `openai` Python SDK using `OPENAI_API_KEY`.
- Enforces grounded system instructions: zero hallucinated incidents/stats, state if evidence is insufficient, distinguish observed facts from interpretations.
- Extracts structured responses cleanly (`answer`, `risk_level`, `confidence`, `affected_zones`, `key_factors`, `evidence`).
- Safely handles missing API keys (`OPENAI_API_KEY`) without crashing or generating fake AI outputs.

### 8. AI Urban Copilot Engine
- **Intent Detection** (`src/processing/copilot_intents.py`): Classifies queries (`CITY_SUMMARY`, `RISK_EXPLANATION`, `ZONE_ANALYSIS`, `EVENT_INVESTIGATION`, `EVENT_COMPARISON`, `TIME_WINDOW_ANALYSIS`, etc.).
- **Human-in-the-Loop Decision Support**: Generates advisory recommendations explicitly marked `"[HUMAN REVIEW RECOMMENDATION]"`.
- **Dashboard Action Binding**: Emits safe client-side actions (`focus_zone`, `view_evidence`, `view_time_window`, `compare_zones`).

### 9. Streamlit Command Center Dashboard
- Professional 2D command-center interface (`src/app/dashboard.py`).
- Displays City Risk Index, Contributing Factors, Zone Intelligence Cards, Live Telemetry Stream, Interactive Map, Analytics, Anomalies Panel, AI Copilot Console, and System Health.

### 10. Human-in-the-Loop Safety Boundary
- The AI is strictly an **operator decision-support system**.
- The Copilot **never** executes autonomous actions, contacts police/ambulance directly, or alters physical traffic signals.
