// Mirrors src/processing/provenance.py; contract tested in pytest.
export type SourceClass = 'REAL' | 'SIMULATED' | 'WEBHOOK' | 'DERIVED' | 'NOT_CONFIGURED';
export type SourceStatus = 'LIVE' | 'SIMULATED' | 'STALE' | 'DEGRADED' | 'OFFLINE' | 'NOT_CONFIGURED';
