// User & Session Authentication Types (§4)
export interface User {
  id: string;
  full_name: string;
  email: string;
  created_at?: string;
  last_login_at?: string;
}

export interface AuthState {
  authenticated: boolean;
  user: User | null;
  loading: boolean;
}

// Provenance Envelopes (§1, §5)
export interface DataFreshness {
  weather_api?: number;
  air_quality_api?: number;
  traffic_simulation?: number;
  webhook?: number;
  [key: string]: number | undefined;
}

export interface DataSourceStatus {
  id: string;
  label: string;
  mode: 'LIVE' | 'SIMULATED' | 'EVENT_DRIVEN' | 'NOT_CONFIGURED';
  status: string;
  last_ok_at: string;
}

export interface WeatherTelemetry {
  temperature?: number;
  condition?: string;
  wind_speed?: number;
  weather_code?: number;
  observed_at?: string;
}

export interface AirQualityTelemetry {
  aqi?: number;
  pm2_5?: number;
  pm10?: number;
  no2?: number;
  observed_at?: string;
}

export interface TrafficTelemetry {
  congestion_level?: number;
  avg_speed_kmh?: number;
  vehicle_count?: number;
  trend?: 'IMPROVING' | 'STABLE' | 'DETERIORATING';
  observed_at?: string;
}

export interface CitySummary {
  city: string;
  state: string;
  lat: number;
  lon: number;
  event_count: number;
  critical_count: number;
  high_count: number;
  anomaly_count: number;
  weather?: WeatherTelemetry;
  air_quality?: AirQualityTelemetry;
  traffic?: TrafficTelemetry;
  risk_score: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
}

export interface TelemetryEvent {
  event_id?: string;
  timestamp: string;
  source: string;
  severity: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  event_type?: string;
  data: Record<string, any>;
  location: {
    city?: string;
    state?: string;
    lat?: number;
    lon?: number;
    latitude?: number;
    longitude?: number;
  };
}

export interface OperationalAnomaly {
  anomaly_id: string;
  type: string;
  source: string;
  description: string;
  severity: string;
  city?: string;
  detected_at: string;
}

export interface Correlation {
  correlation_id: string;
  title: string;
  description: string;
  sources: string[];
  confidence: string;
}

export interface RegionState {
  overall_risk_score: number;
  overall_risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  risk_trend: 'IMPROVING' | 'STABLE' | 'DETERIORATING';
  active_events: number;
  active_anomalies: number;
  cities_online: number;
  cities_total: number;
}

export interface SystemMeta {
  mode: 'HYBRID' | 'LIVE' | 'SIMULATION';
  server_time: string;
  state_version: number;
  pathway: {
    status: string;
    last_batch_at: string;
  };
}

export interface UrbanState {
  meta: SystemMeta;
  region: RegionState;
  sources: DataSourceStatus[];
  city_summaries: Record<string, CitySummary>;
  recent_events: TelemetryEvent[];
  active_anomalies: OperationalAnomaly[];
  correlations: Correlation[];
  data_freshness: DataFreshness;
  overall_risk_score?: number;
  overall_risk_level?: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  risk_trend?: string;
  contributing_factors?: string[];
  last_updated?: string;
}

export interface CopilotEvidence {
  source: string;
  event_type: string;
  city: string;
  observed_at: string;
}

export interface CopilotResponse {
  assessment: string;
  risk: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  answer: string;
  key_factors: string[];
  evidence: CopilotEvidence[];
  human_review: {
    required: boolean;
    reason?: string;
  };
  dashboard_actions?: Array<{
    type: string;
    city?: string;
    label: string;
  }>;
  state_version_used: number;
}
