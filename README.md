# pathway-safety-urban-planning
# Public Safety & Urban Planning with Pathway

Real-time anomaly detection and urban planning system using Pathway's dynamic RAG capabilities.

## Features
- **Public Safety & Anomaly Detection**: 
  - Real-time ingestion of social media, public safety feeds, and IoT sensors
  - Dynamic anomaly detection with configurable rules
  - Live threat monitoring dashboard
  
- **Live Urban Planning Assistant**:
  - Integration with transit, traffic, and environmental APIs
  - Real-time city status visualization
  - Predictive resource allocation insights

## Installation
```bash
git clone https://github.com/hariharasuthan1105/pathway-safety-urban-planning.git
cd pathway-safety-urban-planning
pip install -r requirements.txt
Configuration
Copy and modify the configuration files:
cp config/public_safety.yaml.example config/public_safety.yaml
cp config/urban_planning.yaml.example config/urban_planning.yaml
Usage
Public Safety System
python src/main.py --mode public_safety
Urban planning System
python src/main.py --mode urban_planning
