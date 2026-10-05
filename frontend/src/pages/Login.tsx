import React from 'react';
import { LoginForm } from '../features/auth/LoginForm';
import { ShieldCheck, Activity, MapPin, Cpu } from 'lucide-react';

export const Login: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#070B14] flex flex-col md:flex-row font-sans">
      {/* Desktop Brand Visual Side Panel */}
      <div className="hidden md:flex md:w-1/2 bg-slate-900/60 border-r border-slate-800/80 p-12 flex-col justify-between relative overflow-hidden">
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">URBAN INTELLIGENCE</h1>
              <p className="text-xs font-semibold tracking-widest text-blue-400 uppercase">South India Command Center</p>
            </div>
          </div>

          <div className="space-y-4 max-w-md pt-12">
            <h2 className="text-3xl font-extrabold text-white leading-tight">
              Urban Intelligence for South India
            </h2>
            <p className="text-slate-400 text-sm leading-relaxed">
              Real-time urban intelligence for safer, smarter and more resilient cities. Currently operating across 20 cities in South India.
            </p>
          </div>
        </div>

        <div className="relative z-10 grid grid-cols-3 gap-4 pt-12 border-t border-slate-800/60">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-blue-400 font-medium">
              <MapPin className="w-3.5 h-3.5" />
              <span>Coverage</span>
            </div>
            <p className="text-lg font-bold text-white tabular-nums">20 Cities</p>
            <p className="text-[11px] text-slate-500">TN • KL • AP Nodes</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
              <Activity className="w-3.5 h-3.5" />
              <span>Streaming</span>
            </div>
            <p className="text-lg font-bold text-white tabular-nums">Pathway</p>
            <p className="text-[11px] text-slate-500">Sub-second Stream</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-purple-400 font-medium">
              <Cpu className="w-3.5 h-3.5" />
              <span>AI Engine</span>
            </div>
            <p className="text-lg font-bold text-white tabular-nums">OpenAI</p>
            <p className="text-[11px] text-slate-500">Grounded RAG</p>
          </div>
        </div>
      </div>

      {/* Form Side Panel */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-12 relative z-10">
        <div className="w-full max-w-md space-y-8 glass-surface p-8 md:p-10 rounded-3xl border border-slate-800">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white tracking-tight">Operator Sign In</h2>
            <p className="text-sm text-slate-400">
              Access the live urban operations command center.
            </p>
          </div>

          <LoginForm />
        </div>
      </div>
    </div>
  );
};
