import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { fetchApi } from '../../lib/api';
import type { CopilotResponse } from '../../types';
import { Bot, Send, ChevronRight, FileText, UserCheck } from 'lucide-react';

interface CopilotProps {
  onSelectActionCity?: (city: string) => void;
}

export const CopilotWorkspace: React.FC<CopilotProps> = ({ onSelectActionCity }) => {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuery = async (qText: string) => {
    const q = qText || question;
    if (!q.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await fetchApi<CopilotResponse>('/api/ask', {
        method: 'POST',
        body: JSON.stringify({ question: q }),
      });
      setResponse(data);
    } catch (err: any) {
      setError(err.message || 'Failed to query Copilot');
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    'What is happening across South India right now?',
    'Which city has the highest risk level?',
    'Show active traffic anomalies and congestion spikes',
    'What evidence supports current regional risk?',
    'Check weather & air quality status in Chennai'
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <Card className="p-6 md:p-8 space-y-6 border border-slate-800">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
            <Bot className="w-7 h-7" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Urban Intelligence Copilot</h2>
            <p className="text-xs text-slate-400">
              Ask about live operational state across South India (Grounded RAG + OpenAI).
            </p>
          </div>
        </div>

        {/* Suggested Query Chips */}
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuestion(s);
                handleQuery(s);
              }}
              className="text-xs px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-slate-300 hover:border-blue-500/50 hover:text-white transition-all cursor-pointer"
            >
              {s}
            </button>
          ))}
        </div>

        {/* Query Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleQuery(question);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question (e.g. Why is Madurai at high risk? What should an operator review first?)"
            className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors text-sm"
          />
          <Button type="submit" variant="ai" size="md" isLoading={loading}>
            <Send className="w-4 h-4" />
            <span>Ask</span>
          </Button>
        </form>

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
            Copilot Query Failure: {error}
          </div>
        )}

        {/* Response Card Display */}
        {response && (
          <div className="space-y-6 pt-4 border-t border-slate-800/80">
            {/* Risk & Assessment Banner */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900/90 border border-slate-800">
              <div className="flex items-center gap-3">
                <Badge variant={(response.risk?.toLowerCase() as any) || 'moderate'}>
                  {response.risk || 'MODERATE'} RISK
                </Badge>
                <span className="text-xs text-slate-400 font-medium">Confidence: {response.confidence || 'MEDIUM'}</span>
              </div>
              <span className="text-[11px] text-slate-500 font-mono">
                State Version: {response.state_version_used}
              </span>
            </div>

            {/* Assessment Narrative */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Executive Assessment</h4>
              <p className="text-sm leading-relaxed text-slate-200 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                {response.assessment || response.answer}
              </p>
            </div>

            {/* Key Factors */}
            {response.key_factors && response.key_factors.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Key Operational Factors</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {response.key_factors.map((kf, i) => (
                    <div key={i} className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-300">
                      <ChevronRight className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                      <span>{kf}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Evidence Citations */}
            {response.evidence && response.evidence.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Grounding Evidence Citations</span>
                </h4>
                <div className="space-y-1.5">
                  {response.evidence.map((ev, i) => (
                    <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/60 text-xs">
                      <span className="text-slate-300 font-medium">{ev.city} • {ev.event_type}</span>
                      <span className="text-slate-500 font-mono text-[11px]">{ev.source} | {ev.observed_at}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Human Review Gate */}
            {response.human_review?.required && (
              <div className="flex items-center gap-3 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
                <UserCheck className="w-4 h-4 shrink-0" />
                <span>Human Operator Review Required: {response.human_review.reason || 'Critical operational threshold'}</span>
              </div>
            )}

            {/* Action Chips */}
            {response.dashboard_actions && response.dashboard_actions.length > 0 && (
              <div className="flex gap-2 pt-2">
                {response.dashboard_actions.map((act, i) => (
                  <Button
                    key={i}
                    variant="outline"
                    size="sm"
                    onClick={() => act.city && onSelectActionCity && onSelectActionCity(act.city)}
                  >
                    <span>{act.label}</span>
                  </Button>
                ))}
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};
