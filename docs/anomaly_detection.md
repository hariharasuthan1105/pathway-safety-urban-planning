# Anomaly Detection

This document describes the anomaly detection system used in the Public Safety & Urban Planning system.

## Anomaly Rules

### Public Safety Anomalies
- **Noise Level**: Threshold of 80 dB
- **Crowd Density**: Threshold of 0.8 (80% capacity)
- **Social Media Spike**: 10+ mentions per minute in a location
- **Traffic Flow**: Threshold of 0.2 (20% of normal flow)

### Configuration
Anomaly rules are configured in `config/public_safety.yaml`:

```yaml
anomaly_rules:
  noise_level: 80
  crowd_density: 0.8
  social_media_spike: 10
  traffic_flow: 0.2
