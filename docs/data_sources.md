# Data Sources

This document describes the data sources used in the Public Safety & Urban Planning system.

## Public Safety Data Sources

### Social Media Feeds
- **Source**: Twitter (X) API
- **Data**: Posts containing emergency keywords
- **Fields**: timestamp, text, user, hashtags, location
- **Configuration**: `config/public_safety.yaml`

### Public Safety Feeds
- **Source**: Police and fire scanner APIs
- **Data**: Emergency incidents
- **Fields**: timestamp, type, priority, description, location
- **Configuration**: `config/public_safety.yaml`

### IoT Sensor Data
- **Source**: City sensors (simulated)
- **Data**: Noise levels, crowd density, traffic flow
- **Fields**: timestamp, noise_level, crowd_density, traffic_flow, anomaly, location
- **Configuration**: `config/public_safety.yaml`

## Urban Planning Data Sources

### Transit Data
- **Source**: Public transit APIs
- **Data**: Bus and train locations, delays, passenger counts
- **Fields**: timestamp, route_id, delay, passenger_count, vehicle_location, location
- **Configuration**: `config/urban_planning.yaml`

### Traffic Data
- **Source**: Traffic APIs (TomTom, Google Maps)
- **Data**: Traffic flow, congestion, incidents
- **Fields**: timestamp, congestion_level, average_speed, incident_count, location
- **Configuration**: `config/urban_planning.yaml`

### Environmental Data
- **Source**: Environmental APIs
- **Data**: Air quality, noise levels, temperature
- **Fields**: timestamp, air_quality_index, noise_level, temperature, location
- **Configuration**: `config/urban_planning.yaml`
