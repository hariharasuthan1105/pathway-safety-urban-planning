import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { fetchApi } from '../lib/api';
import type { UrbanState } from '../types';
import { ShieldCheck, Activity, AlertTriangle, Building } from 'lucide-react';

export const Overview: React.FC = () => {
  const { user } = useAuth();
  const [state, setState] = useState<UrbanState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi<UrbanState>('/api/state')
      .then(setState)
      .catch(err => setError(err.message));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Good morning, {user?.full_name || 'Operator'}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Urban Intelligence • South India Command Center. Currently operating across 20 cities in South India.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="blue">MODE: {state?.meta?.mode || 'HYBRID'}</Badge>
          <Badge variant="neutral">20 Cities (TN • KL • AP)</Badge>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          System Connection Offline: {error}
        </div>
      )}

      {/* KPI Metric Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Regional Risk</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-3xl font-extrabold text-white tabular-nums">
            {state?.region?.overall_risk_score ?? '--'}
            <span className="text-sm font-normal text-slate-500">/100</span>
          </p>
          <Badge variant={(state?.region?.overall_risk_level?.toLowerCase() as any) || 'low'}>
            {state?.region?.overall_risk_level || 'SYNCING'}
          </Badge>
        </Card>

        <Card className="p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Ingested Events</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <p className="text-3xl font-extrabold text-white tabular-nums">
            {state?.recent_events?.length ?? '--'}
          </p>
          <span className="text-xs text-blue-400 font-medium">Pathway Stream</span>
        </Card>

        <Card className="p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Anomalies</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-3xl font-extrabold text-white tabular-nums">
            {state?.active_anomalies?.length ?? '--'}
          </p>
          <span className="text-xs text-amber-400 font-medium">Sensor Flags</span>
        </Card>

        <Card className="p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Coverage</span>
            <Building className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-3xl font-extrabold text-white tabular-nums">
            20 Cities
          </p>
          <span className="text-xs text-purple-400 font-medium">TN • KL • AP Nodes</span>
        </Card>
      </div>
    </div>
  );
};
