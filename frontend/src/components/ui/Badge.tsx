import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'low' | 'moderate' | 'high' | 'critical' | 'blue' | 'purple' | 'neutral';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className = ''
}) => {
  const base = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide border';

  const variants = {
    low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    moderate: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    high: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    critical: 'bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse',
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    neutral: 'bg-slate-800/60 text-slate-300 border-slate-700/50'
  };

  return (
    <span className={`${base} ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};
