import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Activity, Cpu, ArrowRight, Zap, Globe, Building2 } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const Landing: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#070B14] text-slate-100 font-sans selection:bg-blue-500/30">
      {/* Navigation Bar */}
      <header className="sticky top-0 z-50 glass-nav h-20 px-6 md:px-12 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight text-white block">URBAN INTELLIGENCE</span>
            <span className="text-[11px] font-semibold tracking-widest text-blue-400 uppercase block -mt-1">South India Platform</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link to="/login">
            <Button variant="ghost" size="sm">Sign In</Button>
          </Link>
          <Link to="/signup">
            <Button variant="primary" size="sm">Explore Platform</Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative px-6 md:px-12 py-20 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div className="space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold tracking-wider uppercase">
            <span>SOUTH INDIA COVERAGE</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold text-white tracking-tight leading-[1.1]">
            Urban Intelligence for South India
          </h1>

          <p className="text-slate-400 text-base md:text-lg leading-relaxed max-w-xl">
            Real-time urban intelligence for safer, smarter and more resilient cities.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link to="/signup">
              <Button variant="primary" size="lg">
                <span>Access Command Center</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" size="lg">
                <span>Sign In as Operator</span>
              </Button>
            </Link>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2 max-w-xl">
            <div className="flex items-center justify-between text-xs font-bold text-white">
              <span className="flex items-center gap-1.5 text-blue-400">
                <Building2 className="w-4 h-4" /> 20 Cities
              </span>
              <span className="text-slate-400 font-medium">Tamil Nadu • Kerala • Andhra Pradesh</span>
            </div>
            <p className="text-xs text-slate-400">
              Currently operating across 20 cities in South India.
            </p>
          </div>
        </div>

        {/* Decorative Visual Card */}
        <div className="relative rounded-3xl glass-surface p-8 border border-slate-800 space-y-6 shadow-2xl">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500 animate-ping" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">Regional Deployment</span>
            </div>
            <span className="text-xs text-blue-400 font-mono">TN • KL • AP</span>
          </div>

          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Globe className="w-5 h-5 text-blue-400" />
                <span className="text-sm font-semibold text-white">Open-Meteo REST Stream</span>
              </div>
              <span className="text-xs text-emerald-400 font-mono">LIVE TELEMETRY</span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-purple-400" />
                <span className="text-sm font-semibold text-white">Traffic Simulation Engine</span>
              </div>
              <span className="text-xs text-purple-400 font-mono">SIMULATED STREAM</span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Cpu className="w-5 h-5 text-indigo-400" />
                <span className="text-sm font-semibold text-white">Grounded RAG + OpenAI</span>
              </div>
              <span className="text-xs text-indigo-400 font-mono">DECISION SUPPORT</span>
            </div>
          </div>
        </div>
      </section>

      {/* Capability Trio Section */}
      <section className="px-6 md:px-12 py-16 bg-slate-950/40 border-t border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <h2 className="text-2xl md:text-3xl font-extrabold text-white">Built for High-Stakes Control Rooms</h2>
            <p className="text-sm text-slate-400">
              Designed for a 2 a.m. control-room operator and a director reading on a mobile device.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl glass-surface space-y-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Globe className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">1. Monitor</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Continuous real-time telemetry across weather, air quality, traffic simulation, and external incident webhooks.
              </p>
            </div>

            <div className="p-6 rounded-2xl glass-surface space-y-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <Zap className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">2. Understand</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Pathway streaming engine evaluates rolling window rates, spatial risk scores, and cross-source correlations.
              </p>
            </div>

            <div className="p-6 rounded-2xl glass-surface space-y-4">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">3. Ask</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Query the AI Urban Copilot for grounded assessment, evidence citations, and human-in-the-loop review criteria.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Data Honesty Section */}
      <section className="px-6 md:px-12 py-16 max-w-7xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-white">Data Honesty Architecture</h2>
          <p className="text-xs text-slate-400">Clear provenance envelopes for every metric displayed in the system.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">LIVE TELEMETRY</span>
            <h4 className="text-sm font-bold text-white">Open-Meteo REST API</h4>
            <p className="text-xs text-slate-400">Live weather and air quality REST telemetry polled for all 20 cities.</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-xs font-bold text-purple-400 uppercase tracking-wider">SIMULATED STREAM</span>
            <h4 className="text-sm font-bold text-white">Traffic Simulation Engine</h4>
            <p className="text-xs text-slate-400">Backend traffic stream with IST peak curves and Open-Meteo weather coupling.</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">EVENT-DRIVEN</span>
            <h4 className="text-sm font-bold text-white">Webhook Ingestion</h4>
            <p className="text-xs text-slate-400">External HTTP webhook incident reports entering Pathway streaming pipeline.</p>
          </div>
        </div>
      </section>
    </div>
  );
};
