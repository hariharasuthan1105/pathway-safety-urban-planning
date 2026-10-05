"""
Standalone HTTP Webhook & Query Server for External Event Ingestion & RAG AI Queries (Phase 3 & Phase 5).

Endpoints:
- POST /events : Receives real-time incident reports & webhook event payloads.
- POST /api/ask : Executes real-time RAG context retrieval and returns structured AI answers.
"""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional, Callable

from .data_sources.real_sources import ingest_webhook_payload
from .processing.shared_state import get_shared_city_state_manager, get_shared_rag_system

logger = logging.getLogger("webhook_server")

# Global handle for AI RAG query handler function
_AI_QUERY_HANDLER: Optional[Callable[[str], Dict[str, Any]]] = None

def register_ai_query_handler(handler: Callable[[str], Dict[str, Any]]):
    """Registers global handler function for POST /api/ask endpoint."""
    global _AI_QUERY_HANDLER
    _AI_QUERY_HANDLER = handler
    logger.info("[Webhook Server] Registered AI RAG query handler for /api/ask.")

class WebhookRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            try:
                city_state_mgr = get_shared_city_state_manager()
                state = city_state_mgr.get_live_city_state()
                response_body = json.dumps(state).encode('utf-8')
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
            except Exception as e:
                logger.error(f"[Webhook Server] GET /api/state error: {e}")
                err_body = json.dumps({"error": str(e)}).encode('utf-8')
                self.send_response(500)
                self.end_headers()
                self.wfile.write(err_body)

        elif self.path == "/api/health":
            try:
                import os
                city_state_mgr = get_shared_city_state_manager()
                state = city_state_mgr.get_live_city_state()
                rag_sys = get_shared_rag_system()
                
                health_data = {
                    "status": "HEALTHY",
                    "pathway_engine": "RUNNING",
                    "data_mode": os.getenv("DATA_MODE", "HYBRID").upper(),
                    "llm_configured": getattr(rag_sys, "has_valid_key", False),
                    "data_freshness": state.get("data_freshness", {}),
                    "total_events_ingested": len(state.get("recent_events", []))
                }
                response_body = json.dumps(health_data).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
            except Exception as e:
                logger.error(f"[Webhook Server] GET /api/health error: {e}")
                err_body = json.dumps({"error": str(e)}).encode('utf-8')
                self.send_response(500)
                self.end_headers()
                self.wfile.write(err_body)

        elif self.path == "/api/risk":
            try:
                city_state_mgr = get_shared_city_state_manager()
                state = city_state_mgr.get_live_city_state()
                risk_data = {
                    "overall_risk_score": state.get("overall_risk_score", 0),
                    "overall_risk_level": state.get("overall_risk_level", "LOW"),
                    "risk_trend": state.get("risk_trend", "STABLE"),
                    "contributing_factors": state.get("contributing_factors", []),
                    "zone_summaries": state.get("zone_summaries", {})
                }
                response_body = json.dumps(risk_data).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
            except Exception as e:
                logger.error(f"[Webhook Server] GET /api/risk error: {e}")
                err_body = json.dumps({"error": str(e)}).encode('utf-8')
                self.send_response(500)
                self.end_headers()
                self.wfile.write(err_body)

        elif self.path == "/api/anomalies":
            try:
                city_state_mgr = get_shared_city_state_manager()
                state = city_state_mgr.get_live_city_state()
                anom_data = {
                    "active_anomalies": state.get("active_anomalies", []),
                    "correlations": state.get("correlations", []),
                    "count": len(state.get("active_anomalies", []))
                }
                response_body = json.dumps(anom_data).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
            except Exception as e:
                logger.error(f"[Webhook Server] GET /api/anomalies error: {e}")
                err_body = json.dumps({"error": str(e)}).encode('utf-8')
                self.send_response(500)
                self.end_headers()
                self.wfile.write(err_body)

        elif self.path == "/api/events":
            try:
                city_state_mgr = get_shared_city_state_manager()
                state = city_state_mgr.get_live_city_state()
                recent_events = state.get("recent_events", [])
                response_body = json.dumps({"events": recent_events, "count": len(recent_events)}).encode('utf-8')

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
            except Exception as e:
                logger.error(f"[Webhook Server] GET /api/events error: {e}")
                err_body = json.dumps({"error": str(e)}).encode('utf-8')
                self.send_response(500)
                self.end_headers()
                self.wfile.write(err_body)
        else:
            self.send_response(404)
            self.end_headers()


    def do_POST(self):
        if self.path == "/events":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                event = ingest_webhook_payload(payload)
                
                response_body = json.dumps({
                    "status": "accepted",
                    "event_id": event["data"].get("event_id"),
                    "timestamp": event["timestamp"],
                    "message": "Event successfully ingested into Pathway streaming pipeline and live city state."
                }).encode('utf-8')
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
                logger.info(f"[Webhook Server] Successfully processed POST /events for type: {event['data'].get('event_type')}")
            
            except Exception as e:
                logger.error(f"[Webhook Server] Failed to process webhook event: {e}")
                err_body = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(err_body)

        elif self.path == "/api/ask":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                payload = json.loads(post_data.decode('utf-8'))
                question = payload.get("question", "")

                if _AI_QUERY_HANDLER:
                    response_data = _AI_QUERY_HANDLER(question)
                else:
                    # Fallback to shared RAG system & shared live city state
                    city_state_mgr = get_shared_city_state_manager()
                    rag_sys = get_shared_rag_system()
                    live_state = city_state_mgr.get_live_city_state()
                    response_data = rag_sys.query_structured(question, city_state=live_state)

                response_body = json.dumps(response_data).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
                logger.info(f"[Webhook Server] Processed POST /api/ask query: '{question}'")

            except Exception as e:
                logger.error(f"[Webhook Server] Failed to process /api/ask query: {e}")
                err_body = json.dumps({
                    "error": str(e),
                    "answer": f"Error processing query: {str(e)}",
                    "risk_level": "UNKNOWN",
                    "confidence": "NONE",
                    "affected_zones": [],
                    "key_factors": [],
                    "evidence": []
                }).encode('utf-8')
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(err_body)

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass

def start_webhook_server(host: str = "0.0.0.0", port: int = 8000, daemon: bool = True) -> HTTPServer:
    """
    Starts the HTTP Webhook ingestion & RAG query server in a background thread.
    """
    server = HTTPServer((host, port), WebhookRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=daemon)
    thread.start()
    logger.info(f"[Webhook Server] Listening for HTTP requests on http://{host}:{port} (/events, /api/ask, /api/state)")
    return server

