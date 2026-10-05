import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { fetchApi } from '../lib/api';
import type { UrbanState } from '../types';
import { Car, RefreshCw, Zap, TrendingDown, TrendingUp, Minus, ShieldAlert, Clock } from 'lucide-react';

export const Traffic: React.FC = () => {
  const [state, setState] = useState<UrbanState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTrafficData = async () => {
    try {
      setLoading(true);
      const data = await fetchApi<UrbanState>('/api/state');
      setState(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch traffic stream');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrafficData();
    const interval = setInterval(fetchTrafficData, 10000);
    return () => clearInterval(interval);
  }, []);

  const citiesList = state?.city_summaries ? Object.values(state.city_summaries) : [];

  // Sort cities by traffic congestion descending (higher congestion level first)
  const sortedCities = [...citiesList].sort((a, b) => {
    const congA = a.traffic?.congestion_level ?? 0;
    const congB = b.traffic?.congestion_level ?? 0;
    return congB - congA;
  });

  const avgSpeedAll = citiesList.length > 0
    ? (citiesList.reduce((acc, c) => acc + (c.traffic?.avg_speed_kmh ?? 0), 0) / citiesList.length).toFixed(1)
    : '--';

  const totalVehicles = citiesList.reduce((acc, c) => acc + (c.traffic?.vehicle_count ?? 0), 0);

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'DETERIORATING': return <TrendingDown className="w-4 h-4 text-rose-400" />;
      case 'IMPROVING': return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      default: return <Minus className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Pipeline Provenance Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <Car className="w-6 h-6 text-blue-400" />
              Traffic Intelligence & Congestion Stream
            </h1>
            <Badge variant="blue" className="font-mono text-[10px] tracking-wider uppercase">
              <Zap className="w-3 h-3 mr-1 animate-pulse" />
              TRAFFIC SIMULATION STREAM
            </Badge>
          </div>
          <p className="text-sm text-slate-400">
            Real-time simulated telemetry stream processing vehicle densities, IST peak curves, and speed dynamics.
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={fetchTrafficData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh Stream
        </Button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Car className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 block font-medium">Regional Average Speed</span>
            <span className="text-2xl font-bold text-white font-mono">{avgSpeedAll} km/h</span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 block font-medium">Monitored Vehicles</span>
            <span className="text-2xl font-bold text-white font-mono">{totalVehicles.toLocaleString()}</span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-600/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs text-slate-400 block font-medium">Active Peak Window</span>
            <span className="text-base font-bold text-amber-300">IST Dynamic Simulation</span>
          </div>
        </Card>
      </div>

      {error && (
        <Card className="border-rose-500/40 bg-rose-950/20 text-rose-300">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span className="text-sm">{error}</span>
          </div>
        </Card>
      )}

      {/* City Congestion Table */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="font-bold text-white text-base">City Congestion Rankings</h3>
          <span className="text-xs text-slate-400">20 Cities Streaming</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider font-semibold">
                <th className="pb-3 px-3">City</th>
                <th className="pb-3 px-3">State</th>
                <th className="pb-3 px-3">Congestion Level</th>
                <th className="pb-3 px-3">Avg Speed</th>
                <th className="pb-3 px-3">Vehicle Volume</th>
                <th className="pb-3 px-3">Trend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {sortedCities.map((city) => {
                const cong = city.traffic?.congestion_level ?? 0;
                return (
                  <tr key={city.city} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-3 font-sans font-bold text-white">{city.city}</td>
                    <td className="py-3 px-3 font-sans text-slate-400">{city.state}</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-3">
                        <div className="w-24 bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              cong > 70 ? 'bg-rose-500' : cong > 40 ? 'bg-amber-500' : 'bg-emerald-500'
                            }`}
                            style={{ width: `${Math.min(100, cong)}%` }}
                          />
                        </div>
                        <span className="font-bold text-slate-200">{cong.toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-slate-300">{city.traffic?.avg_speed_kmh ?? '--'} km/h</td>
                    <td className="py-3 px-3 text-slate-300">{city.traffic?.vehicle_count?.toLocaleString() ?? '--'}</td>
                    <td className="py-3 px-3 flex items-center gap-1 font-sans">
                      {getTrendIcon(city.traffic?.trend)}
                      <span className="text-[11px] text-slate-400">{city.traffic?.trend || 'STABLE'}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
