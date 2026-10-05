import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { fetchApi } from '../lib/api';
import type { UrbanState, CitySummary } from '../types';
import { 
  Building2, Search, Thermometer, 
  Car, ShieldAlert, Activity, X, RefreshCw, BarChart2 
} from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export const Cities: React.FC = () => {
  const [state, setState] = useState<UrbanState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedState, setSelectedState] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCity, setSelectedCity] = useState<CitySummary | null>(null);
  const [cityHistory, setCityHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const fetchStateData = async () => {
    try {
      setLoading(true);
      const data = await fetchApi<UrbanState>('/api/state');
      setState(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch city state');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStateData();
    const interval = setInterval(fetchStateData, 10000);
    return () => clearInterval(interval);
  }, []);

  const openCityDetail = async (city: CitySummary) => {
    setSelectedCity(city);
    setLoadingHistory(true);
    try {
      const cityId = city.city.toLowerCase().replace(/\s+/g, '_');
      const historyRes = await fetchApi<{ history: any[] }>(`/api/cities/${cityId}/history`);
      setCityHistory(historyRes.history || []);
    } catch {
      setCityHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const citiesList = state?.city_summaries ? Object.values(state.city_summaries) : [];

  const filteredCities = citiesList.filter((c) => {
    const matchesState = selectedState === 'ALL' || c.state.toUpperCase() === selectedState;
    const matchesSearch = c.city.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          c.state.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesState && matchesSearch;
  });

  const getRiskBadge = (level: string) => {
    switch (level) {
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
            <Building2 className="w-6 h-6 text-blue-400" />
            City Telemetry & Regional Coverage
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Currently operating across 20 cities in South India (Tamil Nadu, Kerala, and Andhra Pradesh).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchStateData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 glass-surface p-4 rounded-2xl border border-slate-800">
        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
          {['ALL', 'TAMIL NADU', 'KERALA', 'ANDHRA PRADESH'].map((st) => (
            <button
              key={st}
              onClick={() => setSelectedState(st)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                selectedState === st
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search city..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Error state */}
      {error && (
        <Card className="border-rose-500/40 bg-rose-950/20 text-rose-300">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span className="text-sm">{error}</span>
          </div>
        </Card>
      )}

      {/* Cities Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredCities.map((city) => (
          <Card
            key={city.city}
            className="hover:border-blue-500/40 transition-all cursor-pointer group"
            onClick={() => openCityDetail(city)}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-bold text-lg text-white group-hover:text-blue-400 transition-colors">
                  {city.city}
                </h3>
                <span className="text-xs text-slate-400 font-medium">{city.state}</span>
              </div>
              {getRiskBadge(city.risk_level)}
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs py-3 border-y border-slate-800/80 my-3">
              <div className="space-y-1">
                <span className="text-slate-400 block">Risk Score</span>
                <span className="font-mono text-base font-bold text-white">{city.risk_score?.toFixed(1)}</span>
              </div>
              <div className="space-y-1">
                <span className="text-slate-400 block">AQI Index</span>
                <span className="font-mono text-base font-bold text-slate-200">
                  {city.air_quality?.aqi ?? '--'}
                </span>
              </div>
              <div className="space-y-1">
                <span className="text-slate-400 block">Weather</span>
                <span className="text-slate-200 flex items-center gap-1 font-medium">
                  <Thermometer className="w-3.5 h-3.5 text-amber-400" />
                  {city.weather?.temperature ? `${city.weather.temperature.toFixed(1)}°C` : '--'}
                </span>
              </div>
              <div className="space-y-1">
                <span className="text-slate-400 block">Traffic Speed</span>
                <span className="text-slate-200 flex items-center gap-1 font-medium">
                  <Car className="w-3.5 h-3.5 text-blue-400" />
                  {city.traffic?.avg_speed_kmh ? `${city.traffic.avg_speed_kmh} km/h` : '--'}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
              <span>{city.event_count} telemetry events</span>
              <span className="text-blue-400 font-medium group-hover:underline flex items-center gap-1">
                View History <BarChart2 className="w-3 h-3" />
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* City Detail Modal */}
      {selectedCity && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-[#0b1329] border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 space-y-6 shadow-2xl relative">
            <button
              onClick={() => setSelectedCity(null)}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{selectedCity.city}</h2>
                <p className="text-xs text-slate-400">{selectedCity.state} • Lat {selectedCity.lat}, Lon {selectedCity.lon}</p>
              </div>
              <div className="ml-auto pr-8">
                {getRiskBadge(selectedCity.risk_level)}
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 block">Risk Score</span>
                <span className="text-lg font-bold text-white font-mono">{selectedCity.risk_score?.toFixed(1)}</span>
              </div>
              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 block">Temperature</span>
                <span className="text-lg font-bold text-amber-400 font-mono">
                  {selectedCity.weather?.temperature ? `${selectedCity.weather.temperature.toFixed(1)}°C` : '--'}
                </span>
              </div>
              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 block">AQI Index</span>
                <span className="text-lg font-bold text-emerald-400 font-mono">
                  {selectedCity.air_quality?.aqi ?? '--'}
                </span>
              </div>
              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 block">Avg Speed</span>
                <span className="text-lg font-bold text-blue-400 font-mono">
                  {selectedCity.traffic?.avg_speed_kmh ? `${selectedCity.traffic.avg_speed_kmh} km/h` : '--'}
                </span>
              </div>
            </div>

            {/* Telemetry Timeline Chart */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-400" />
                Historical Risk & Metric Trend
              </h4>

              {loadingHistory ? (
                <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
                  Loading historical telemetry...
                </div>
              ) : cityHistory.length > 0 ? (
                <div className="h-56 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={cityHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="timestamp" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                      <Line type="monotone" dataKey="risk_score" name="Risk Score" stroke="#ef4444" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="aqi" name="AQI" stroke="#10b981" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-32 flex items-center justify-center text-slate-500 text-xs bg-slate-950/40 rounded-xl border border-slate-800">
                  Real-time history accumulated over pipeline updates.
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="outline" size="sm" onClick={() => setSelectedCity(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
