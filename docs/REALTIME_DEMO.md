# Real-Time Event & AI Copilot Demonstration Guide

This guide provides exact step-by-step instructions for verifying that live events flow continuously from HTTP webhook ingestion and external telemetry connectors into the Pathway streaming engine, update the Live City State, and dynamically modify AI Copilot responses and evidence citations in real time.

---

## Prerequisites

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

---

## Step 1: Start the Backend & Webhook Ingestion Server

Run the system entry point in `public_safety` or `urban_planning` mode:

```bash
python -m src.main --mode public_safety
```

Expected Output:
```text
[INFO] Application starting...
[INFO] [Webhook Server] Listening for HTTP requests on http://0.0.0.0:8000 (/events, /api/ask, /api/state)
[INFO] Data sources connected...
[INFO] Pathway streaming pipeline starting...
```

---

## Step 2: Start the Command Center Dashboard (Optional / Parallel)

In a separate terminal, launch the Streamlit command center dashboard:

```bash
streamlit run src/app/dashboard.py
```

The dashboard will connect to `http://localhost:8000/api/state` and `http://localhost:8000/api/ask`.

---

## Step 3: Verify Initial Baseline State

Check current live city state via curl or PowerShell:

```bash
curl http://localhost:8000/api/state
```

Alternatively, ask the AI Copilot via REST API:

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is happening in the city right now?"}'
```

---

## Step 4: Inject Real-Time Event #1 (`REALTIME_TEST_001`)

Inject a severe vehicle collision event into `POST /events`:

```bash
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "REALTIME_TEST_001",
    "event_type": "vehicle_collision",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "severity": "CRITICAL",
    "source": "webhook_ingestion",
    "data": {
      "event_id": "REALTIME_TEST_001",
      "event_type": "vehicle_collision",
      "severity": "CRITICAL",
      "description": "Multi-car pileup causing major road closure in Zone A (Downtown)",
      "priority": 5
    }
  }'
```

### Verification #1:

Query the AI Copilot immediately after posting `REALTIME_TEST_001`:

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is happening in the city right now?"}'
```

**Expected Result**:
- Response `answer` explicitly references `REALTIME_TEST_001` and the multi-car pileup in Zone A.
- `risk_level` reflects the critical incident.
- `evidence` citations array includes `{ "event_id": "REALTIME_TEST_001", "source": "webhook_ingestion", "zone": "Zone A (Downtown)", "severity": "CRITICAL" }`.

---

## Step 5: Inject Real-Time Event #2 (`REALTIME_TEST_002`)

Inject a different high-severity air quality / gas leak event in Midtown (Zone B):

```bash
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "REALTIME_TEST_002",
    "event_type": "air_quality",
    "latitude": 40.7580,
    "longitude": -73.9855,
    "severity": "HIGH",
    "source": "webhook_ingestion",
    "data": {
      "event_id": "REALTIME_TEST_002",
      "event_type": "hazardous_gas_leak",
      "severity": "HIGH",
      "description": "Chemical gas leak detected in Midtown industrial building",
      "air_quality_index": 185
    }
  }'
```

### Verification #2:

Query the AI Copilot for the latest significant event:

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the latest significant event?"}'
```

**Expected Result**:
- Response `answer` updates dynamically to feature `REALTIME_TEST_002` and the hazardous gas leak in Zone B.
- `evidence` citations array updates to cite `REALTIME_TEST_002`.

---

## Step 6: Automated Integration Test Execution

You can also run the automated end-to-end real-time integration test suite anytime:

```bash
pytest tests/test_realtime_dataflow.py -v
```
