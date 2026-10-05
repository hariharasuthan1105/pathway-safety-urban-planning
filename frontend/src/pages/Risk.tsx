import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { fetchApi } from '../lib/api';
import type { UrbanState, OperationalAnomaly, Correlation } from '../types';
import { ShieldAlert, AlertTriangle, RefreshCw, Layers } from 'lucide-react';

export const Risk: React.FC = () => {
  const [state, setState] = useState<UrbanState | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchRiskData = async () => {
    try {
      setLoading(true);
      const data = await fetchApi<UrbanState>('/api/state');
      setState(data);
    } catch {
      // Handled gracefully in UI
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskData();
    const interval = setInterval(fetchRiskData, 10000);
    return () => clearInterval(interval);
  }, []);

  const anomalies: OperationalAnomaly[] = state?.active_anomalies || [];
  const correlations: Correlation[] = state?.correlations || [];
  const regionalRiskScore = state?.region?.overall_risk_score ?? state?.overall_risk_score ?? 0;
  const regionalRiskLevel = state?.region?.overall_risk_level ?? state?.overall_risk_level ?? 'LOW';

  const getRiskBadge = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL': return <Badge variant="critical">CRITICAL</Badge>;
      case 'HIGH': return <Badge variant="high">HIGH</Badge>;
      case 'MODERATE': return <Badge variant="moderate">MODERATE</Badge>;
      default: return <Badge variant="low">LOW</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-rose-400" />
            Regional Risk & Anomaly Intelligence
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Pathway sliding-window anomaly detection and cross-telemetry correlation models.
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={fetchRiskData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh Risk Pipeline
        </Button>
      </div>

      {/* Regional Risk Meter Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1 space-y-4 bg-gradient-to-br from-slate-900/90 to-rose-950/20 border-rose-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Overall Regional Score</span>
            {getRiskBadge(regionalRiskLevel)}
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-5xl font-black text-white font-mono">{regionalRiskScore.toFixed(1)}</span>
            <span className="text-xs text-slate-400">/ 100 index</span>
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-800">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Risk Severity Index</span>
              <span>{regionalRiskScore > 70 ? 'Hazard' : regionalRiskScore > 40 ? 'Elevated' : 'Normal'}</span>
            </div>
            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  regionalRiskScore > 70 ? 'bg-rose-500' : regionalRiskScore > 40 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, Math.max(5, regionalRiskScore))}%` }}
              />
            </div>
          </div>
        </Card>

        {/* Trigger Correlations */}
        <Card className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="font-bold text-white text-base flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              Cross-Stream Correlations
            </h3>
            <span className="text-xs text-slate-400">{correlations.length} Active Correlations</span>
          </div>

          <div className="space-y-3">
            {correlations.length > 0 ? (
              correlations.map((corr) => (
                <div key={corr.correlation_id} className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-white">{corr.title}</span>
                    <Badge variant="blue" className="text-[10px]">{corr.confidence} Confidence</Badge>
                  </div>
                  <p className="text-xs text-slate-300">{corr.description}</p>
                  <div className="flex items-center gap-2 pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Sources: {corr.sources?.join(', ') || 'Multi-source'}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-6 text-center text-slate-500 text-xs bg-slate-950/40 rounded-xl border border-slate-800">
                No active multi-stream hazard correlations detected in current window.
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Active Anomalies Feed */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Detected Operational Anomalies
          </h3>
          <span className="text-xs text-slate-400">{anomalies.length} Anomalies</span>
        </div>

        <div className="space-y-3">
          {anomalies.length > 0 ? (
            anomalies.map((anom) => (
              <div key={anom.anomaly_id} className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-white">{anom.type}</span>
                    {anom.city && <span className="text-xs text-blue-400 font-medium">• {anom.city}</span>}
                  </div>
                  <p className="text-xs text-slate-300">{anom.description}</p>
                  <span className="text-[11px] text-slate-500 font-mono block">
                    Source: {anom.source} • Detected: {new Date(anom.detected_at).toLocaleTimeString()}
                  </span>
                </div>
                {getRiskBadge(anom.severity)}
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs bg-slate-950/40 rounded-xl border border-slate-800">
              Pipeline state clear — zero active anomaly flags present.
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
