import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { fetchApi } from '../lib/api';
import type { CopilotResponse } from '../types';
import { Bot, Send, Sparkles, ShieldCheck, AlertCircle, FileText, CheckCircle2 } from 'lucide-react';

export const Copilot: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const presetQueries = [
    'What is the current operational risk in Chennai?',
    'Summarize recent traffic anomalies across Kochi and Thiruvananthapuram.',
    'Are there any environmental hazard spikes in Visakhapatnam?',
    'What is the air quality outlook for Coimbatore?',
  ];

  const handleAsk = async (promptQuery?: string) => {
    const q = promptQuery || query;
    if (!q.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await fetchApi<CopilotResponse>('/api/ask', {
        method: 'POST',
        body: JSON.stringify({ query: q }),
      });
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'Failed to query Grounded Copilot');
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadgeVariant = (risk?: string) => {
    switch (risk?.toUpperCase()) {
      case 'CRITICAL': return 'critical';
      case 'HIGH': return 'high';
      case 'MODERATE': return 'moderate';
      default: return 'low';
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Bot className="w-6 h-6 text-blue-400" />
          Grounded Urban Decision Copilot
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          RAG intelligence powered strictly by live Pathway streaming state envelopes and verified evidence logs.
        </p>
      </div>

      {/* Query Bar */}
      <Card className="space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk();
          }}
          className="flex items-center gap-3"
        >
          <input
            type="text"
            placeholder="Ask Copilot (e.g. 'What is the risk level in Madurai and what parameters drive it?')"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <Button type="submit" disabled={loading || !query.trim()}>
            {loading ? (
              <Sparkles className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Send className="w-4 h-4 mr-2" />
            )}
            Analyze
          </Button>
        </form>

        {/* Preset Prompts */}
        <div className="space-y-2">
          <span className="text-xs text-slate-400 font-semibold block">Preset Operator Prompts:</span>
          <div className="flex flex-wrap gap-2">
            {presetQueries.map((pq) => (
              <button
                key={pq}
                onClick={() => {
                  setQuery(pq);
                  handleAsk(pq);
                }}
                className="px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 hover:text-white hover:border-blue-500/40 transition-all text-left"
              >
                "{pq}"
              </button>
            ))}
          </div>
        </div>
      </Card>

      {error && (
        <Card className="border-rose-500/40 bg-rose-950/20 text-rose-300">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400" />
            <span className="text-sm">{error}</span>
          </div>
        </Card>
      )}

      {/* Copilot Response Card */}
      {response && (
        <Card className="space-y-6 border-blue-500/30 bg-gradient-to-br from-slate-900/90 to-blue-950/20">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-base">Copilot Grounded Synthesis</h3>
                <span className="text-xs text-slate-400 font-mono">State Version {response.state_version_used}</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Badge variant={getRiskBadgeVariant(response.risk)}>
                RISK: {response.risk}
              </Badge>
              <Badge variant="blue">
                CONFIDENCE: {response.confidence}
              </Badge>
            </div>
          </div>

          {/* Answer Text */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Assessment & Answer</h4>
            <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">
              {response.answer || response.assessment}
            </div>
          </div>

          {/* Key Contributing Factors */}
          {response.key_factors && response.key_factors.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Key Contributing Telemetry Factors</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {response.key_factors.map((kf, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 bg-slate-900/60 rounded-lg border border-slate-800 text-xs text-slate-300">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{kf}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evidence Provenance */}
          {response.evidence && response.evidence.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-indigo-400" />
                Grounded Evidence Envelopes ({response.evidence.length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 font-mono text-xs">
                {response.evidence.map((ev, idx) => (
                  <div key={idx} className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                    <div className="flex justify-between text-blue-400 font-bold">
                      <span>{ev.city || 'Regional'}</span>
                      <span className="text-[10px] text-slate-400">{ev.event_type}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">Source: {ev.source}</p>
                    <p className="text-[10px] text-slate-500">Observed: {new Date(ev.observed_at).toLocaleTimeString()}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};
