"""
Central Shared Runtime State Manager for CityStateManager and RAGSystem.

Ensures that Webhook Server (/events, /api/ask), Pathway Streaming Engine,
Data Sources, and Streamlit Dashboard all access the exact same live runtime state.
"""

import threading
import logging
from typing import Dict, Any, Optional

from .city_state import CityStateManager
from .rag_system import RAGSystem

logger = logging.getLogger("shared_state")

_STATE_LOCK = threading.Lock()
_SHARED_CITY_STATE_MANAGER: Optional[CityStateManager] = None
_SHARED_RAG_SYSTEM: Optional[RAGSystem] = None

def get_shared_city_state_manager(config: Optional[Dict[str, Any]] = None) -> CityStateManager:
    """Retrieves or initializes the global thread-safe CityStateManager singleton."""
    global _SHARED_CITY_STATE_MANAGER
    with _STATE_LOCK:
        if _SHARED_CITY_STATE_MANAGER is None:
            logger.info("[SharedState] Initializing global CityStateManager singleton.")
            _SHARED_CITY_STATE_MANAGER = CityStateManager(config or {})
        elif config and not _SHARED_CITY_STATE_MANAGER.config:
            _SHARED_CITY_STATE_MANAGER.config = config
    return _SHARED_CITY_STATE_MANAGER

def get_shared_rag_system(config: Optional[Dict[str, Any]] = None) -> RAGSystem:
    """Retrieves or initializes the global thread-safe RAGSystem singleton."""
    global _SHARED_RAG_SYSTEM
    with _STATE_LOCK:
        if _SHARED_RAG_SYSTEM is None:
            logger.info("[SharedState] Initializing global RAGSystem singleton.")
            _SHARED_RAG_SYSTEM = RAGSystem(config or {})
        elif config and not _SHARED_RAG_SYSTEM.config:
            _SHARED_RAG_SYSTEM.config = config
    return _SHARED_RAG_SYSTEM

def ingest_runtime_event(event: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Unified entry point for ingesting a runtime event into both CityStateManager and RAGSystem.
    """
    mgr = get_shared_city_state_manager(config)
    rag = get_shared_rag_system(config)
    
    processed = mgr.ingest_event(event)
    data = processed.get("data", {}) if isinstance(processed.get("data"), dict) else {}
    source = processed.get("source", "unknown")
    location = processed.get("location", {}) if isinstance(processed.get("location"), dict) else {}
    
    rag.add_document(data, source, location)
    logger.debug(f"[SharedState] Ingested event {data.get('event_id', 'unk')} into shared state.")
    return processed

def reset_shared_state():
    """Resets shared singletons (used primarily for unit testing clean slates)."""
    global _SHARED_CITY_STATE_MANAGER, _SHARED_RAG_SYSTEM
    with _STATE_LOCK:
        _SHARED_CITY_STATE_MANAGER = None
        _SHARED_RAG_SYSTEM = None
        logger.info("[SharedState] Reset global shared singletons.")
