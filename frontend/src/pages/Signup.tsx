import React from 'react';
import { SignupForm } from '../features/auth/SignupForm';
import { ShieldCheck, Lock, Globe } from 'lucide-react';

export const Signup: React.FC = () => {
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
              <h1 className="text-xl font-bold tracking-tight text-white">SOUTH INDIA</h1>
              <p className="text-xs font-semibold tracking-widest text-blue-400 uppercase">Urban Intelligence Platform</p>
            </div>
          </div>

          <div className="space-y-4 max-w-md pt-12">
            <h2 className="text-3xl font-extrabold text-white leading-tight">
              Enterprise Access Request
            </h2>
            <p className="text-slate-400 text-sm leading-relaxed">
              Create an operator account to monitor live public safety, environmental metrics, and AI decision support across Tamil Nadu, Kerala, and Andhra Pradesh.
            </p>
          </div>
        </div>

        <div className="relative z-10 space-y-3 pt-12 border-t border-slate-800/60 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            <span>Encrypted Session Cookies & PBKDF2 Password Hashing</span>
          </div>
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-blue-400" />
            <span>20 South Indian Metropolitan Regions Supported</span>
          </div>
        </div>
      </div>

      {/* Form Side Panel */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-12 relative z-10">
        <div className="w-full max-w-md space-y-6 glass-surface p-8 md:p-10 rounded-3xl border border-slate-800">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white tracking-tight">Operator Sign Up</h2>
            <p className="text-sm text-slate-400">
              Register new credentials for urban operations.
            </p>
          </div>

          <SignupForm />
        </div>
      </div>
    </div>
  );
};
