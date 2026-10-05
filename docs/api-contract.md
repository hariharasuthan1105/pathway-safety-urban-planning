# South India Urban Intelligence — API Contract Specification

Version: 1.0.0
Base URL: `http://localhost:8000`

---

## 1. Authentication Endpoints

All session cookies are `HTTP-only`, `Secure` (in HTTPS), with `SameSite=Lax` (or `None` for cross-site CORS).

### `POST /api/auth/signup`
Creates a new user account.

**Request**:
```json
{
  "full_name": "Control Room Operator",
  "email": "operator@urbanintel.in",
  "password": "SecurePassword123!"
}
```

**Response (201 Created)**:
```json
{
  "user": {
    "id": "usr_9b1e2a",
    "full_name": "Control Room Operator",
    "email": "operator@urbanintel.in",
    "created_at": "2026-10-05T18:50:00Z"
  },
  "message": "Account created successfully"
}
```

### `POST /api/auth/login`
Authenticates a user and sets the `session_token` HTTP-only cookie.

**Request**:
```json
{
  "email": "operator@urbanintel.in",
  "password": "SecurePassword123!",
  "remember": true
}
```

**Response (200 OK)**:
```json
{
  "user": {
    "id": "usr_9b1e2a",
    "full_name": "Control Room Operator",
    "email": "operator@urbanintel.in",
    "last_login_at": "2026-10-05T18:50:00Z"
  }
}
```

### `GET /api/auth/me`
Retrieves currently authenticated session user profile.

**Response (200 OK)**:
```json
{
  "authenticated": true,
  "user": {
    "id": "usr_9b1e2a",
    "full_name": "Control Room Operator",
    "email": "operator@urbanintel.in"
  }
}
```

**Response (401 Unauthorized)**:
```json
{
  "authenticated": false,
  "error": "Session expired or invalid"
}
```

### `POST /api/auth/logout`
Invalidates session and clears cookie.

**Response (200 OK)**:
```json
{
  "message": "Logged out successfully"
}
```

---

## 2. Real-Time Operational State & Telemetry

### `GET /api/state`
Returns complete real-time urban state with provenance envelopes across 20 South Indian cities.
Requires valid session cookie.

**Response (200 OK)**:
```json
{
  "meta": {
    "mode": "HYBRID",
    "server_time": "2026-10-05T18:50:00Z",
    "state_version": 1420,
    "pathway": {
      "status": "RUNNING",
      "last_batch_at": "2026-10-05T18:49:58Z"
    }
  },
  "region": {
    "overall_risk_score": 42,
    "overall_risk_level": "MODERATE",
    "risk_trend": "STABLE",
    "active_events": 14,
    "active_anomalies": 2,
    "cities_online": 20,
    "cities_total": 20
  },
  "sources": [
    { "id": "weather_api", "label": "WEATHER API (OPEN-METEO)", "mode": "LIVE", "status": "LIVE", "last_ok_at": "2026-10-05T18:49:55Z" },
    { "id": "air_quality_api", "label": "AIR QUALITY API (OPEN-METEO)", "mode": "LIVE", "status": "LIVE", "last_ok_at": "2026-10-05T18:49:55Z" },
    { "id": "traffic_simulation", "label": "TRAFFIC SIMULATION STREAM", "mode": "SIMULATED", "status": "LIVE", "last_ok_at": "2026-10-05T18:49:59Z" },
    { "id": "webhook", "label": "WEBHOOK INGESTION", "mode": "EVENT_DRIVEN", "status": "IDLE", "last_ok_at": "2026-10-05T18:45:00Z" },
    { "id": "gtfs_transit", "label": "GTFS TRANSIT INTERFACE", "mode": "NOT_CONFIGURED", "status": "NOT_CONFIGURED", "last_ok_at": "N/A" }
  ],
  "city_summaries": {
    "Chennai": {
      "city": "Chennai",
      "state": "Tamil Nadu",
      "lat": 13.0827,
      "lon": 80.2707,
      "event_count": 3,
      "critical_count": 0,
      "high_count": 1,
      "anomaly_count": 0,
      "weather": { "temperature": 30.3, "condition": "Clear Sky", "wind_speed": 8.0, "observed_at": "2026-10-05T18:49:50Z" },
      "air_quality": { "aqi": 64, "pm2_5": 14.4, "pm10": 20.4, "no2": 4.2, "observed_at": "2026-10-05T18:49:50Z" },
      "traffic": { "congestion_level": 0.45, "avg_speed_kmh": 28.5, "vehicle_count": 1420, "trend": "STABLE", "observed_at": "2026-10-05T18:49:59Z" },
      "risk_score": 38,
      "risk_level": "MODERATE"
    }
  },
  "recent_events": [],
  "active_anomalies": [],
  "correlations": [],
  "data_freshness": { "weather_api": 5, "traffic_simulation": 1 }
}
```

### `GET /api/stream` (SSE)
Server-Sent Events stream delivering real-time state deltas.

**Event Format**:
```text
event: state_update
data: {"state_version": 1421, "timestamp": "2026-10-05T18:50:03Z", "updated_cities": ["Chennai"], ...}
```

### `GET /api/cities/{city_id}/history`
Returns historical timeseries metrics for a specified city.

**Parameters**:
- `metric`: `risk` | `traffic` | `weather` | `air_quality`
- `window`: `15m` | `1h` | `24h`

---

## 3. Webhook Event Ingestion

### `POST /events`
Public/authenticated endpoint for external event ingestion.

**Request**:
```json
{
  "event_type": "crowd_density",
  "severity": "CRITICAL",
  "location": {
    "city": "Madurai",
    "state": "Tamil Nadu",
    "lat": 9.9252,
    "lon": 78.1198
  },
  "details": {
    "density": 950,
    "description": "Massive crowd congestion at temple entrance"
  }
}
```

**Response (200 OK)**:
```json
{
  "status": "INGESTED",
  "event_id": "wh_a71b8e",
  "timestamp": "2026-10-05T18:50:00Z"
}
```

---

## 4. AI Grounded Copilot

### `POST /api/ask`
Queries Grounded RAG + OpenAI LLM using current state.

**Request**:
```json
{
  "question": "What is the safety and traffic status in Madurai right now?"
}
```

**Response (200 OK)**:
```json
{
  "assessment": "Madurai is currently experiencing HIGH risk due to severe crowd density near Meenakshi Temple.",
  "risk": "HIGH",
  "confidence": "HIGH",
  "answer": "Grounded RAG analysis indicates a crowd density spike of 950 persons/min in Madurai...",
  "key_factors": ["Crowd density spike", "Congestion level 0.78"],
  "evidence": [
    {
      "source": "webhook",
      "event_type": "crowd_density",
      "city": "Madurai",
      "observed_at": "2026-10-05T18:50:00Z"
    }
  ],
  "human_review": {
    "required": true,
    "reason": "Critical crowd density exceeds safety threshold"
  },
  "dashboard_actions": [
    { "type": "SELECT_CITY", "city": "madurai", "label": "Inspect Madurai State" }
  ],
  "state_version_used": 1421
}
```
