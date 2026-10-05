import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { fetchApi } from '../lib/api';
import type { UrbanState } from '../types';
import { CloudSun, Thermometer, Wind, RefreshCw, ShieldAlert, Droplets, Activity } from 'lucide-react';

export const Environment: React.FC = () => {
  const [state, setState] = useState<UrbanState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedState, setSelectedState] = useState<string>('ALL');

  const fetchEnvData = async () => {
    try {
      setLoading(true);
      const data = await fetchApi<UrbanState>('/api/state');
      setState(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch environmental state');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnvData();
    const interval = setInterval(fetchEnvData, 10000);
    return () => clearInterval(interval);
  }, []);

  const citiesList = state?.city_summaries ? Object.values(state.city_summaries) : [];
  const filteredCities = citiesList.filter(
    (c) => selectedState === 'ALL' || c.state.toUpperCase() === selectedState
  );

  const getAqiBadge = (aqi?: number) => {
    if (aqi === undefined) return <Badge variant="neutral">N/A</Badge>;
    if (aqi <= 50) return <Badge variant="low">GOOD ({aqi})</Badge>;
    if (aqi <= 100) return <Badge variant="moderate">MODERATE ({aqi})</Badge>;
    if (aqi <= 150) return <Badge variant="high">UNHEALTHY ({aqi})</Badge>;
    return <Badge variant="critical">HAZARDOUS ({aqi})</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <CloudSun className="w-6 h-6 text-emerald-400" />
              Environmental Intelligence & Air Quality
            </h1>
            <Badge variant="low" className="font-mono text-[10px] tracking-wider uppercase">
              Open-Meteo Telemetry
            </Badge>
          </div>
          <p className="text-sm text-slate-400">
            Real-time environmental telemetry streaming Open-Meteo weather parameters and atmospheric air quality metrics.
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={fetchEnvData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh Pipeline
        </Button>
      </div>

      {/* State Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {['ALL', 'TAMIL NADU', 'KERALA', 'ANDHRA PRADESH'].map((st) => (
          <button
            key={st}
            onClick={() => setSelectedState(st)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
              selectedState === st
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {error && (
        <Card className="border-rose-500/40 bg-rose-950/20 text-rose-300">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span className="text-sm">{error}</span>
          </div>
        </Card>
      )}

      {/* Environmental Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredCities.map((city) => (
          <Card key={city.city} className="space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-bold text-base text-white">{city.city}</h3>
                <span className="text-xs text-slate-400">{city.state}</span>
              </div>
              {getAqiBadge(city.air_quality?.aqi)}
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs py-3 border-y border-slate-800/80 my-2">
              <div className="space-y-1">
                <span className="text-slate-400 block flex items-center gap-1">
                  <Thermometer className="w-3 h-3 text-amber-400" /> Temp
                </span>
                <span className="font-mono text-sm font-bold text-white">
                  {city.weather?.temperature ? `${city.weather.temperature.toFixed(1)}°C` : '--'}
                </span>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 block flex items-center gap-1">
                  <Wind className="w-3 h-3 text-blue-400" /> Wind
                </span>
                <span className="font-mono text-sm font-bold text-slate-200">
                  {city.weather?.wind_speed ? `${city.weather.wind_speed.toFixed(1)} km/h` : '--'}
                </span>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 block flex items-center gap-1">
                  <Activity className="w-3 h-3 text-emerald-400" /> PM 2.5
                </span>
                <span className="font-mono text-sm font-bold text-slate-200">
                  {city.air_quality?.pm2_5 ? `${city.air_quality.pm2_5.toFixed(1)} µg/m³` : '--'}
                </span>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 block flex items-center gap-1">
                  <Droplets className="w-3 h-3 text-cyan-400" /> PM 10
                </span>
                <span className="font-mono text-sm font-bold text-slate-200">
                  {city.air_quality?.pm10 ? `${city.air_quality.pm10.toFixed(1)} µg/m³` : '--'}
                </span>
              </div>
            </div>

            <div className="text-[11px] text-slate-500 font-mono flex items-center justify-between">
              <span>Observed: {city.weather?.observed_at ? new Date(city.weather.observed_at).toLocaleTimeString() : 'Live'}</span>
              <span>{city.weather?.condition || 'Clear'}</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
