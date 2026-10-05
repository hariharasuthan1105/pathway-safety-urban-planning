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

logger = logging.getLogger("webhook_server")

# Global handle for AI RAG query handler function
_AI_QUERY_HANDLER: Optional[Callable[[str], Dict[str, Any]]] = None

def register_ai_query_handler(handler: Callable[[str], Dict[str, Any]]):
    """Registers global handler function for POST /api/ask endpoint."""
    global _AI_QUERY_HANDLER
    _AI_QUERY_HANDLER = handler
    logger.info("[Webhook Server] Registered AI RAG query handler for /api/ask.")

class WebhookRequestHandler(BaseHTTPRequestHandler):
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
                    "message": "Event successfully ingested into Pathway streaming pipeline."
                }).encode('utf-8')
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
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
                    response_data = {
                        "error": "HANDLER_NOT_REGISTERED",
                        "answer": "AI RAG backend query handler is not registered yet.",
                        "risk_level": "UNKNOWN",
                        "confidence": "NONE",
                        "affected_zones": [],
                        "key_factors": [],
                        "evidence": []
                    }

                response_body = json.dumps(response_data).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
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

    def log_message(self, format, *args):
        pass

def start_webhook_server(host: str = "0.0.0.0", port: int = 8000, daemon: bool = True) -> HTTPServer:
    """
    Starts the HTTP Webhook ingestion & RAG query server in a background thread.
    """
    server = HTTPServer((host, port), WebhookRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=daemon)
    thread.start()
    logger.info(f"[Webhook Server] Listening for HTTP POST on http://{host}:{port} (/events & /api/ask)")
    return server
