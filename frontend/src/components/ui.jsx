import React from 'react';

export function DistressScore({ score }) {
  const getColor = (s) => {
    if (s >= 80) return 'text-rose-700 bg-rose-50 border-rose-200';
    if (s >= 60) return 'text-amber-700 bg-amber-50 border-amber-200';
    if (s >= 40) return 'text-yellow-700 bg-yellow-50 border-yellow-200';
    return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  };

  const getBar = (s) => {
    if (s >= 80) return 'bg-rose-500';
    if (s >= 60) return 'bg-amber-500';
    if (s >= 40) return 'bg-yellow-500';
    return 'bg-[#0F4C3A]';
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`border rounded-full px-2.5 py-0.5 text-xs font-bold tabular-nums ${getColor(score)}`}>
        {score != null ? score.toFixed(1) : '—'}
      </div>
      <div className="w-14 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${getBar(score)}`}
          style={{ width: `${Math.min(score || 0, 100)}%` }}
        />
      </div>
    </div>
  );
}

export function RiskBadge({ level }) {
  const classes = {
    critical: 'bg-rose-50 text-rose-700 border border-rose-200/80 rounded-full px-2.5 py-0.5 text-xs font-semibold',
    high: 'bg-amber-50 text-amber-700 border border-amber-200/80 rounded-full px-2.5 py-0.5 text-xs font-semibold',
    moderate: 'bg-yellow-50 text-yellow-700 border border-yellow-200/80 rounded-full px-2.5 py-0.5 text-xs font-semibold',
    low: 'bg-emerald-50 text-emerald-700 border border-emerald-200/80 rounded-full px-2.5 py-0.5 text-xs font-semibold',
  };
  return (
    <span className={classes[level?.toLowerCase()] || 'bg-slate-50 text-slate-600 border border-slate-200 rounded-full px-2.5 py-0.5 text-xs font-semibold'}>
      {level || 'low'}
    </span>
  );
}

export function TrendArrow({ trend }) {
  if (!trend || trend === 'stable') {
    return <span className="text-slate-400 font-medium text-xs bg-slate-100 px-2 py-0.5 rounded-full">→ stable</span>;
  }
  if (trend === 'worsening') {
    return <span className="text-rose-600 font-medium text-xs bg-rose-50 px-2 py-0.5 rounded-full flex items-center gap-0.5">↑ worsening</span>;
  }
  return <span className="text-emerald-700 font-medium text-xs bg-emerald-50 px-2 py-0.5 rounded-full flex items-center gap-0.5">↓ improving</span>;
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center h-32">
      <div className="w-8 h-8 border-3 border-[#0F4C3A] border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export function EmptyState({ message = 'No data available' }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-slate-400">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
        <span className="text-xl">📋</span>
      </div>
      <p className="text-sm font-medium text-slate-600">{message}</p>
    </div>
  );
}
