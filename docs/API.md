# REAL-TIME URBAN INTELLIGENCE PLATFORM — BACKEND API DOCUMENTATION

The platform provides a standalone HTTP server (`src/webhook_server.py`) running on default port `8000` supporting incident ingestion and real-time AI Copilot query endpoints.

---

## 1. Incident Webhook Ingestion API

### Endpoint
`POST /events`

### Description
Ingests real-time incident reports, emergency scanner alerts, or external sensor payloads into the Pathway streaming graph.

### Request Headers
`Content-Type: application/json`

### Example Request Body
```json
{
  "event_type": "vehicle_collision",
  "severity": "CRITICAL",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "source": "police_scanner",
  "data": {
    "description": "3-vehicle collision blocking two lanes on Main Street",
    "vehicles_involved": 3
  }
}
```

### Example Response Body (`200 OK`)
```json
{
  "status": "accepted",
  "event_id": "wh_a1b2c3d4",
  "timestamp": "2026-10-05T16:00:00.000000+00:00",
  "message": "Event successfully ingested into Pathway streaming pipeline."
}
```

---

## 2. AI Urban Copilot & RAG Query API

### Endpoint
`POST /api/ask`

### Description
Queries the real-time grounded RAG context and OpenAI LLM provider to receive structured copilot analysis, evidence audit trails, Human-in-the-Loop decision recommendations, and dashboard focus actions.

### Request Headers
`Content-Type: application/json`

### Example Request Body
```json
{
  "question": "Why is Zone A currently at high risk?"
}
```

### Example Response Body (`200 OK`)
```json
{
  "answer": "Zone A (Downtown) is currently at CRITICAL risk (Score: 100/100) due to a 3-vehicle collision blocking traffic during heavy rainfall.",
  "intent": "ZONE_ANALYSIS",
  "risk_score": 100,
  "risk_level": "CRITICAL",
  "confidence": "HIGH",
  "affected_zones": [
    "Zone A (Downtown)"
  ],
  "key_factors": [
    "1 critical vehicle collision reported via webhook",
    "Gridlock traffic detected on traffic API",
    "Cross-source corroboration across 3 independent sources"
  ],
  "recommended_actions": [
    "[HUMAN REVIEW RECOMMENDATION] Priority review recommended for overall city risk state (CRITICAL).",
    "[HUMAN REVIEW RECOMMENDATION] Operator inspection advised for high-risk zones: Zone A (Downtown)."
  ],
  "evidence": [
    {
      "event_id": "p6_wh1",
      "source": "webhook_ingestion",
      "timestamp": "2026-10-05T16:32:00Z",
      "zone": "Zone A (Downtown)",
      "severity": "CRITICAL"
    }
  ],
  "dashboard_actions": [
    {
      "action": "focus_zone",
      "label": "📍 Focus Map on Zone A (Downtown)",
      "target": "Zone A (Downtown)"
    },
    {
      "action": "view_evidence",
      "label": "🔍 View Incidents in Zone A (Downtown)",
      "target": "Zone A (Downtown)"
    }
  ]
}
```
