"""Manual HTTP smoke test against a running local backend; creates one test account."""
import os
import time
import uuid
import requests

base = os.getenv("SMOKE_API_URL", "http://127.0.0.1:10000").rstrip("/")
session = requests.Session()
def check(method, path, expected=200, **kwargs):
    response = session.request(method, base + path, timeout=30, **kwargs)
    assert response.status_code == expected, f"{method} {path}: {response.status_code}"
    print(f"PASS {method} {path}: {expected}")
    return response.json() if response.content else None

check("GET", "/api/health")
check("GET", "/api/state", 401)
email = f"smoke_{uuid.uuid4().hex}@example.com"
password = "LocalSmokeTest123!"
check("POST", "/api/auth/signup", 201, json={"full_name":"Local Smoke Operator", "email":email, "password":password})
check("GET", "/api/auth/me")
state = check("GET", "/api/state")
assert len(state["city_summaries"]) == 20
initial = state["meta"]["state_version"]
event_id = f"smoke-{uuid.uuid4().hex}"
result = check("POST", "/events", json={"event_id":event_id, "event_type":"verification_incident", "source":"qa_webhook", "latitude":13.0827123, "longitude":80.2707456, "severity":"HIGH", "data":{"city":"Chennai", "description":"Local verification record"}})
assert result["event_id"] == event_id
answer = check("POST", "/api/ask", json={"question":"Why is Chennai at risk? Summarise the available evidence."})
assert answer["provider"] in {"deterministic_fallback", "groq"}
print("Copilot provider:", answer["provider"])
history = check("GET", "/api/cities/Chennai/history?metric=congestion")
assert isinstance(history["data_points"], list)
print("Recorded congestion observations:", len(history["data_points"]))
check("POST", "/api/auth/logout")
check("GET", "/api/state", 401)
check("POST", "/api/auth/login", json={"email":email, "password":password})
time.sleep(2)
state = check("GET", "/api/state")
assert state["meta"]["state_version"] > initial
check("GET", "/api/health")
print("PASS stream advances; 20 city summaries available")
