# PROJECT PRESENTATION — REAL-TIME URBAN INTELLIGENCE PLATFORM

---

## Slide 1: Title & Overview
- **Project Title**: Real-Time Urban Intelligence Engine & AI Copilot Platform
- **Tagline**: Streaming Telemetry, Deterministic Risk Intelligence, and Human-in-the-Loop AI Decision Support powered by Pathway and RAG.
- **Presenter**: Engineering Team

---

## Slide 2: The Problem Statement
- **Urban Complexity**: Modern cities generate massive streams of fragmented telemetry (weather, air quality, traffic, scanner alerts, webhooks).
- **Latency & Silos**: Incident management teams struggle with delayed data integration, static reports, and siloed dashboard tools.
- **High Stakes**: Crisis management requires instant spatial-temporal awareness without sacrificing factual accuracy.

---

## Slide 3: Limitations of Traditional Approaches
- **Batch Processing Delay**: Traditional ETL pipelines update every 15–60 minutes, missing rapid incident spikes.
- **Ungrounded AI Hallucinations**: Standard LLM chatbots invent emergency incidents, fake stats, or claim autonomous authority.
- **Black-Box Scoring**: Complex opaque ML models fail to explain *why* a risk score changed.

---

## Slide 4: Proposed Solution
- **Unified Telemetry**: Normalizes heterogeneous feeds into standardized `CityEvent` streams.
- **Pathway Streaming Pipeline**: In-memory streaming tables with parallel UDF rule evaluation.
- **Deterministic Risk Engine**: Explainable 0–100 risk scoring with transparent factor weighting and audit trails.
- **Human-in-the-Loop AI Copilot**: Grounded real-time RAG context, explicit operator recommendations, and safe UI focus actions.

---

## Slide 5: End-to-End System Architecture
```
Data Sources (Weather, Air Quality, Webhooks, Simulators)
        ↓
CityEvent Normalization Schema
        ↓
Pathway Streaming Graph (pw.Table concat & UDFs)
        ↓
Real-Time Intelligence Engine (Rolling Windows, Zone Intelligence, Risk Scoring, Correlator)
        ↓
Live City State (Risk Index 0-100, Evidence Trail, Zone Summaries)
        ↓
Real-Time Grounded RAG Context Assembler
        ↓
OpenAI LLM Provider (Direct SDK Integration)
        ↓
AI Urban Copilot Engine (Intents, Human Review Recommendations, UI Action Bindings)
        ↓
Streamlit Operations Command Center
```

---

## Slide 6: Real-Time Pathway Streaming Pipeline
- **Streaming Table Engine**: Uses `pw.Table` to ingest live streams from Python generators (`pw.io.python.read`).
- **Parallel UDF Evaluation**: Rule-based anomaly detection UDFs process incoming rows without blocking.
- **Multi-Mode Support**: Seamless execution in `LIVE`, `SIMULATION`, and `HYBRID` modes.

---

## Slide 7: Urban Risk & Anomaly Intelligence Engine
- **Rolling Sliding Windows**: 5m, 15m, 30m, and 60m rate tracking with acceleration ratio calculation.
- **Geographic Zone Intelligence**: Spatial bucketing mapping coordinates to zones (Downtown, Midtown, Uptown, Outer District).
- **Transparent Risk Scoring**: Deterministic 0–100 score (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) with factor breakdowns.
- **Cross-Source Correlation**: Detects multi-source incident overlaps (weather + traffic + webhook) in short time windows.

---

## Slide 8: Real-Time Grounded RAG + OpenAI Synthesis
- **Dynamic Context Assembler**: Formats the up-to-the-second **Live City State** into structured prompt context.
- **Strict Grounding Directives**: Enforces zero hallucinated incidents/stats, notes if evidence is insufficient, and distinguishes facts from interpretation.
- **Structured Output**: Returns JSON payloads with explicit fields (`answer`, `risk_level`, `confidence`, `affected_zones`, `evidence`).

---

## Slide 9: AI Urban Copilot & Human-in-the-Loop Safety
- **Decision Support Only**: All AI recommendations are prefixed with `[HUMAN REVIEW RECOMMENDATION]`.
- **Zero Autonomous Execution**: Safety filters strictly prevent claims of autonomous police dispatch or traffic control.
- **Safe Dashboard UI Actions**: One-click action buttons (`📍 Focus Map on Zone A`, `🔍 View Incidents in Zone A`).

---

## Slide 10: Live Multi-Source Demonstration Scenario
- **Scenario Setup**:
  1. Heavy Rain event (Weather API)
  2. Gridlock Traffic event (Traffic API)
  3. Vehicle Collision [CRITICAL] (Webhook API)
- **Live State Result**: City Risk Index jumps to `100/100 (CRITICAL)`, Cross-source correlation flagged.
- **Copilot Query**: Operator asks *"Why is Zone A critical?"* -> Copilot responds with grounded explanation and verified audit evidence citations.

---

## Slide 11: Verification & Regression Testing Results
- **Pytest Suite**: 31 passed in 1.79 seconds (`100% success`).
- **Data Mode Reliability**: Verified clean execution across `LIVE`, `HYBRID`, and `SIMULATION` modes.
- **Security Audit**: Zero real API keys or credentials committed; `.env` excluded in `.gitignore`.

---

## Slide 12: Future Roadmap
- **Persistent Time-Series Storage**: Integrating PostgreSQL / TimescaleDB for multi-month trend analysis.
- **GIS Polygon Boundary Support**: Replacing bounding-box zones with exact spatial GeoJSON polygons.
- **Multi-Agency API Connectors**: Adding GTFS-realtime transit and emergency CAD feeds.
