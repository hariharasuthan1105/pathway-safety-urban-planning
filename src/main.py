import argparse
import sys
import os
import yaml
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Add the parent directory to sys.path so packages can be imported cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

try:
    import pathway as pw
except ImportError:
    from src.pathway_compat import pw

from src.data_sources import DataSourceManager
from src.processing import AnomalyDetector, RAGSystem, CityStateManager
from src.app import Dashboard
from src.webhook_server import start_webhook_server, register_ai_query_handler

def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        example_path = Path(f"{config_path}.example")
        if example_path.exists():
            logger.info(f"Config file {config_path} not found. Falling back to example config: {example_path}")
            path = example_path
        else:
            raise FileNotFoundError(f"Configuration file not found at {config_path} or {example_path}")
    
    logger.info(f"Loading configuration from {path}")
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and 'llm' in config:
        config['llm']['api_key'] = openai_key

    return config

def main():
    logger.info("Application starting (Phase 3 Real-Time Telemetry & Webhook Ingestion)...")
    parser = argparse.ArgumentParser(description='Public Safety & Urban Planning System')
    parser.add_argument('--mode', choices=['public_safety', 'urban_planning'], default='public_safety',
                        help='System mode to run (default: public_safety)')
    parser.add_argument('--config', type=str, 
                        help='Path to configuration file')
    
    args = parser.parse_args()
    
    config_path = args.config if args.config else f"config/{args.mode}.yaml"
    
    try:
        config = load_config(config_path)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    data_mode = os.getenv("DATA_MODE", config.get("data_mode", "hybrid")).upper()
    logger.info(f"System initialized in mode: {config.get('mode', args.mode)} | DATA_MODE: {data_mode}")
    
    # Start HTTP Webhook server in background thread
    try:
        webhook_port = int(os.getenv("WEBHOOK_PORT", config.get("webhook_port", 8000)))
        start_webhook_server(port=webhook_port)
    except Exception as e:
        logger.warning(f"Failed to launch Webhook HTTP server on port {webhook_port}: {e}")

    # Initialize data sources
    logger.info("Initializing data sources...")
    data_manager = DataSourceManager(config)
    data_streams = data_manager.get_streams()
    connector_status = data_manager.get_connector_status()
    config['connector_status'] = connector_status
    config['data_mode'] = data_mode

    logger.info(f"Data sources connected. Active streams: {len(data_streams)} | Connectors: {list(connector_status.keys())}")
    
    # Initialize processing components
    logger.info("Initializing anomaly detector...")
    anomaly_detector = AnomalyDetector(config)
    
    logger.info("Initializing City State Intelligence Engine...")
    city_state_manager = CityStateManager(config)

    logger.info("Initializing RAG system...")
    rag_system = RAGSystem(config)
    if rag_system.has_valid_key:
        logger.info("LLM configuration detected: Valid OpenAI key found.")
    else:
        logger.warning("LLM configuration detected: OPENAI_API_KEY missing or placeholder.")
    
    # Register AI query handler for POST /api/ask endpoint
    def handle_ai_query(question: str) -> dict:
        live_state = city_state_manager.get_live_city_state()
        return rag_system.query_structured(question, city_state=live_state)

    register_ai_query_handler(handle_ai_query)
    
    # Build Pathway pipeline
    logger.info("Pathway pipeline starting...")
    if data_streams:
        if hasattr(pw.Table, "concat_by_name"):
            combined_table = pw.Table.concat_by_name(*data_streams)
        else:
            combined_table = pw.Table.concat(data_streams)
    else:
        combined_table = pw.Table()

    # Process data
    processed_table = combined_table.select(
        timestamp=combined_table.timestamp,
        source=combined_table.source,
        data=anomaly_detector.process(combined_table.data),
        location=combined_table.location
    )
    
    # Ingest processed rows into RAG System & City State Manager
    for row in processed_table.collect():
        city_state_manager.ingest_event(row)
        rag_system.add_document(row.get('data', {}), row.get('source', ''), row.get('location', {}))
        logger.info(f"Event processed from source: {row.get('source')}")
    
    # Filter anomalies
    anomalies_table = processed_table.filter(
        pw.this.data.get("anomaly", False)
    )
    
    # Output results
    pw.io.csv.write(anomalies_table, "anomalies.csv")
    pw.io.json.write(processed_table, "processed_data.json")
    
    # Start dashboard
    logger.info("Frontend/API starting...")
    dashboard = Dashboard(processed_table, anomalies_table, rag_system, config, city_state_manager=city_state_manager)
    dashboard.run()
    logger.info("Application shutdown completed cleanly.")

if __name__ == "__main__":
    main()
