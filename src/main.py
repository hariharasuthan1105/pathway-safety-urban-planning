import argparse
import sys
import os
import yaml
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_sources import DataSourceManager
from processing import AnomalyDetector, RAGSystem
from app import Dashboard

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description='Public Safety & Urban Planning System')
    parser.add_argument('--mode', choices=['public_safety', 'urban_planning'], required=True,
                        help='System mode to run')
    parser.add_argument('--config', type=str, 
                        help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Determine config file path
    if args.config:
        config_path = args.config
    else:
        config_path = f"config/{args.mode}.yaml"
    
    # Load configuration
    config = load_config(config_path)
    
    # Initialize data sources
    data_manager = DataSourceManager(config)
    data_streams = data_manager.get_streams()
    
    # Initialize processing components
    anomaly_detector = AnomalyDetector(config)
    rag_system = RAGSystem(config)
    
    # Build Pathway pipeline
    import pathway as pw
    
    combined_table = pw.Table.concat(data_streams)
    
    # Process data
    processed_table = combined_table.select(
        combined_table.timestamp,
        combined_table.source,
        data=anomaly_detector.process(combined_table.data),
        combined_table.location
    )
    
    # Update RAG system
    processed_table = processed_table.select(
        processed_table.timestamp,
        processed_table.source,
        processed_table.data,
        processed_table.location,
        _=rag_system.add_document(processed_table.data, processed_table.source, processed_table.location)
    )
    
    # Filter anomalies
    anomalies_table = processed_table.filter(
        pw.this.data.get("anomaly", False)
    )
    
    # Output results
    pw.io.csv.write(anomalies_table, "anomalies.csv")
    pw.io.json.write(processed_table, "processed_data.json")
    
    # Start dashboard
    dashboard = Dashboard(processed_table, anomalies_table, rag_system, config)
    dashboard.run()

if __name__ == "__main__":
    main()
