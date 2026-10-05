import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'glass' | 'solid' | 'bordered';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'glass',
  className = '',
  ...props
}) => {
  const baseStyles = 'rounded-2xl transition-all duration-200';

  const variants = {
    glass: 'glass-surface shadow-xl',
    solid: 'bg-slate-900 border border-slate-800 shadow-lg',
    bordered: 'bg-slate-950/60 border border-slate-800/80 hover:border-slate-700'
  };

  return (
    <div className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
      {children}
    </div>
  );
};
