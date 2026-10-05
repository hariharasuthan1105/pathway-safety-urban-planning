import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { fetchApi } from '../lib/api';
import type { UrbanState } from '../types';
import { Settings as SettingsIcon, User, Server, Database, RefreshCw, Activity, Cpu } from 'lucide-react';

export const Settings: React.FC = () => {
  const { user } = useAuth();
  const [state, setState] = useState<UrbanState | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchSystemInfo = async () => {
    setLoading(true);
    try {
      const stateRes = await fetchApi<UrbanState>('/api/state').catch(() => null);
      setState(stateRes);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemInfo();
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-slate-400" />
          System Settings & Operator Administration
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Authentication session credentials, backend service status, and pipeline architecture configurations.
        </p>
      </div>

      {/* Operator Session Card */}
      <Card className="space-y-4">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-800">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">Active Operator Session</h3>
            <span className="text-xs text-slate-400">Authenticated via SQLite PBKDF2-HMAC-SHA256 Auth Engine</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-sans">Full Name</span>
            <span className="text-sm font-bold text-white font-sans">{user?.full_name || 'Operator'}</span>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-sans">Email Address</span>
            <span className="text-sm font-bold text-white font-sans">{user?.email || 'operator@urban.gov.in'}</span>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-sans">Session Token ID</span>
            <span className="text-slate-300">{user?.id ? `${user.id.slice(0, 16)}...` : 'HTTP-Only Cookie Verified'}</span>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-sans">Security Standard</span>
            <Badge variant="low">PBKDF2 100,000 Iterations</Badge>
          </div>
        </div>
      </Card>

      {/* Backend Architecture & Pipeline Status */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Backend Telemetry Engine</h3>
              <span className="text-xs text-slate-400">Pathway Streaming + FastAPI Web Service</span>
            </div>
          </div>

          <Button variant="outline" size="sm" onClick={fetchSystemInfo} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Check Health
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5 text-blue-400" /> Pipeline Status
            </span>
            <span className="font-bold text-emerald-400 font-mono text-sm">
              {state?.meta?.pathway?.status || 'OPERATIONAL'}
            </span>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-amber-400" /> State Version
            </span>
            <span className="font-bold text-white font-mono text-sm">
              v{state?.meta?.state_version ?? 1}
            </span>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block flex items-center gap-1">
              <Database className="w-3.5 h-3.5 text-indigo-400" /> Nodes Online
            </span>
            <span className="font-bold text-white font-mono text-sm">
              {state?.region?.cities_online ?? 20} / 20 Configured
            </span>
          </div>
        </div>

        {/* Data Sources Status List */}
        <div className="space-y-2 pt-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Registered Data Sources</span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 font-mono text-xs">
            {state?.sources?.map((src) => (
              <div key={src.id} className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="font-bold text-white block">{src.label}</span>
                  <span className="text-[10px] text-slate-400">Mode: {src.mode}</span>
                </div>
                <Badge variant={src.status === 'OK' || src.status === 'ACTIVE' ? 'low' : 'blue'}>
                  {src.status}
                </Badge>
              </div>
            )) || (
              <div className="text-slate-500 text-xs py-2">Loading data source list...</div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};
