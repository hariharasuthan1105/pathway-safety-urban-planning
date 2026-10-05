import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { fetchApi } from '../lib/api';
import type { UrbanState, TelemetryEvent } from '../types';
import { Zap, Search, RefreshCw, Filter, ShieldAlert, Code } from 'lucide-react';

export const Events: React.FC = () => {
  const [state, setState] = useState<UrbanState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEventRaw, setSelectedEventRaw] = useState<TelemetryEvent | null>(null);

  const fetchEventsData = async () => {
    try {
      setLoading(true);
      const data = await fetchApi<UrbanState>('/api/state');
      setState(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch event stream');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEventsData();
    const interval = setInterval(fetchEventsData, 5000);
    return () => clearInterval(interval);
  }, []);

  const events: TelemetryEvent[] = state?.recent_events || [];

  const filteredEvents = events.filter((ev) => {
    const matchesSev = severityFilter === 'ALL' || ev.severity?.toUpperCase() === severityFilter;
    const cityStr = ev.location?.city || '';
    const srcStr = ev.source || '';
    const typeStr = ev.event_type || '';
    const matchesSearch = cityStr.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          srcStr.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          typeStr.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSev && matchesSearch;
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev?.toUpperCase()) {
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
            <Zap className="w-6 h-6 text-amber-400" />
            Live Stream Event Audit
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time telemetry event stream processed through Pathway sliding-window pipeline.
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={fetchEventsData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh Audit Feed
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 glass-surface p-4 rounded-2xl border border-slate-800">
        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
          <Filter className="w-4 h-4 text-slate-400 mr-1" />
          {['ALL', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                severityFilter === sev
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search event type, city..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
          />
        </div>
      </div>

      {error && (
        <Card className="border-rose-500/40 bg-rose-950/20 text-rose-300">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span className="text-sm">{error}</span>
          </div>
        </Card>
      )}

      {/* Events Table */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="font-bold text-white text-base">Telemetry Stream Payload Log</h3>
          <span className="text-xs text-slate-400">{filteredEvents.length} Recent Events</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider font-semibold">
                <th className="pb-3 px-3">Timestamp</th>
                <th className="pb-3 px-3">City / Location</th>
                <th className="pb-3 px-3">Event Type</th>
                <th className="pb-3 px-3">Source</th>
                <th className="pb-3 px-3">Severity</th>
                <th className="pb-3 px-3 text-right">Raw Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {filteredEvents.length > 0 ? (
                filteredEvents.map((ev, index) => (
                  <tr key={ev.event_id || index} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-3 text-slate-400">
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-3 font-sans font-bold text-white">
                      {ev.location?.city || 'Regional'}
                    </td>
                    <td className="py-3 px-3 text-slate-200">
                      {ev.event_type || 'telemetry_reading'}
                    </td>
                    <td className="py-3 px-3 text-blue-400">
                      {ev.source || 'Pathway Pipeline'}
                    </td>
                    <td className="py-3 px-3">
                      {getSeverityBadge(ev.severity)}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => setSelectedEventRaw(ev)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                        title="View JSON Payload"
                      >
                        <Code className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                    No matching streaming events found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Raw JSON Payload Modal */}
      {selectedEventRaw && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-[#0b1329] border border-slate-800 rounded-2xl w-full max-w-xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <Code className="w-5 h-5 text-amber-400" />
                Raw Telemetry Payload Envelope
              </h3>
              <button
                onClick={() => setSelectedEventRaw(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-emerald-400 font-mono text-xs overflow-x-auto max-h-96">
              {JSON.stringify(selectedEventRaw, null, 2)}
            </pre>
            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setSelectedEventRaw(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
