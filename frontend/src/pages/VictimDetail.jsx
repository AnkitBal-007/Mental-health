import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  fetchVictimById,
  fetchVictimCheckIns,
  fetchVictimRecommendations,
  evaluateAlert,
} from '../api/client';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { DistressScore, RiskBadge, Spinner } from '../components/ui';
import {
  ArrowLeft, Zap, Shield, Heart, Landmark, Banknote, Scale, RefreshCw,
  AlertTriangle, CheckCircle, Clock, Activity,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';

const CATEGORY_ICONS = {
  protection: Shield,
  counselling: Heart,
  medical: Activity,
  relocation: Landmark,
  financial: Banknote,
  legal_aid: Scale,
};

const CATEGORY_COLORS = {
  protection: 'border-rose-200 bg-rose-50/70 text-rose-800',
  counselling: 'border-purple-200 bg-purple-50/70 text-purple-800',
  medical: 'border-blue-200 bg-blue-50/70 text-blue-800',
  relocation: 'border-amber-200 bg-amber-50/70 text-amber-800',
  financial: 'border-emerald-200 bg-emerald-50/70 text-emerald-800',
  legal_aid: 'border-cyan-200 bg-cyan-50/70 text-cyan-800',
};

const PRIORITY_BADGE = {
  immediate: 'bg-rose-100 text-rose-700 border-rose-200',
  high: 'bg-amber-100 text-amber-700 border-amber-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  routine: 'bg-slate-100 text-slate-600 border-slate-200',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const score = payload[0]?.value;
  return (
    <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 shadow-md">
      <p className="text-xs text-slate-400 font-medium mb-1">{label}</p>
      <p className="text-lg font-extrabold text-slate-900 tabular-nums">{score?.toFixed(1)}</p>
      <p className={`text-xs font-bold ${score >= 70 ? 'text-rose-600' : score >= 50 ? 'text-amber-600' : 'text-emerald-700'}`}>
        {score >= 70 ? '⚠ High distress' : score >= 50 ? '⚡ Moderate' : '✓ Stable'}
      </p>
    </div>
  );
};

export default function VictimDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [victim, setVictim] = useState(null);
  const [checkIns, setCheckIns] = useState([]);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [alertLoading, setAlertLoading] = useState(false);
  const [alertResult, setAlertResult] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [v, ci, rec] = await Promise.all([
        fetchVictimById(id),
        fetchVictimCheckIns(id, 30),
        fetchVictimRecommendations(id),
      ]);
      setVictim(v);
      setCheckIns(ci || []);
      setRecommendations(rec);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const handleEvaluateAlert = async () => {
    setAlertLoading(true);
    setAlertResult(null);
    try {
      const res = await evaluateAlert(id);
      setAlertResult(res);
    } catch (e) {
      setAlertResult({ error: e.message });
    } finally {
      setAlertLoading(false);
    }
  };

  const chartData = [...checkIns]
    .reverse()
    .map((ci) => ({
      date: ci.timestamp ? format(parseISO(ci.timestamp), 'dd MMM') : '',
      score: ci.distress_score ?? 0,
      emotion: ci.emotion_label,
    }));

  if (loading) return (
    <div className="p-8">
      <Spinner />
    </div>
  );

  if (error) return (
    <div className="p-8 text-rose-600 text-sm font-semibold">{error}</div>
  );

  if (!victim) return null;

  return (
    <div className="max-w-6xl mx-auto space-y-7 pb-12 animate-fade-in">
      {/* Back + Header */}
      <div>
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-slate-500 hover:text-slate-800 text-xs font-bold mb-4 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1.5">
              <h1 className="text-2xl font-extrabold text-slate-900 font-mono tracking-tight">{victim.id}</h1>
              <RiskBadge level={victim.risk_level} />
            </div>
            <p className="text-slate-500 text-xs font-semibold capitalize">
              {victim.case_type?.replace(/_/g, ' ')} · Registered {victim.registration_date ? format(parseISO(victim.registration_date), 'dd MMM yyyy') : '—'} · {victim.assigned_district}
            </p>
          </div>
          <div className="flex gap-2.5">
            <button
              onClick={load}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold border border-slate-200 shadow-2xs transition-all active:scale-95 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
            <button
              onClick={handleEvaluateAlert}
              disabled={alertLoading}
              className="flex items-center gap-2 px-5 py-2 rounded-full bg-[#0F4C3A] hover:bg-[#0A392B] text-white text-xs font-bold shadow-sm transition-all active:scale-95 cursor-pointer disabled:opacity-50"
            >
              <Zap className="w-3.5 h-3.5 text-emerald-200" />
              {alertLoading ? 'Evaluating…' : 'Evaluate Alert'}
            </button>
          </div>
        </div>

        {alertResult && (
          <div className={`mt-4 flex items-center gap-2 rounded-2xl px-4 py-3 text-xs font-semibold border ${
            alertResult.error
              ? 'bg-rose-50 border-rose-200 text-rose-700'
              : alertResult.alert_id
                ? 'bg-amber-50 border-amber-200 text-amber-800'
                : 'bg-emerald-50 border-emerald-200 text-emerald-800'
          }`}>
            {alertResult.error
              ? <><AlertTriangle className="w-4 h-4" /> {alertResult.error}</>
              : alertResult.alert_id
                ? <><AlertTriangle className="w-4 h-4" /> Alert triggered — Score: {alertResult.distress_score?.toFixed(1)}, Escalation: {(alertResult.escalation_probability * 100).toFixed(0)}%</>
                : <><CheckCircle className="w-4 h-4" /> Within thresholds — no alert triggered</>
            }
          </div>
        )}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Distress Score', value: <DistressScore score={victim.current_distress_score ?? 0} /> },
          { label: 'Escalation Prob.', value: `${((victim.escalation_probability ?? 0) * 100).toFixed(0)}%` },
          { label: 'Trend', value: <span className="capitalize">{victim.score_trend || 'stable'}</span> },
          { label: 'Check-Ins', value: checkIns.length },
        ].map(({ label, value }) => (
          <div key={label} className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm">
            <p className="text-[11px] font-bold text-slate-400 mb-1 uppercase tracking-wider">{label}</p>
            <div className="text-xl font-extrabold text-slate-900">{value}</div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Distress Chart */}
        <div className="lg:col-span-3 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#0F4C3A]" />
            Distress Score Over Time
          </h2>
          {chartData.length === 0 ? (
            <p className="text-slate-400 text-xs text-center py-12">No check-in data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={230}>
              <LineChart data={chartData} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Alert', position: 'right', fontSize: 10, fill: '#ef4444' }} />
                <ReferenceLine y={50} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'Watch', position: 'right', fontSize: 10, fill: '#f59e0b' }} />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#0F4C3A"
                  strokeWidth={2.5}
                  dot={{ r: 3.5, fill: '#0F4C3A', strokeWidth: 0 }}
                  activeDot={{ r: 6, fill: '#10B981', stroke: '#fff', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Factor Breakdown */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            Contributing Factors
          </h2>
          {recommendations?.contributing_factors_evaluated?.length > 0 ? (
            <div className="space-y-3">
              {recommendations.contributing_factors_evaluated.map((factor, i) => {
                const barWidth = Math.max(20, 100 - i * 12);
                return (
                  <div key={factor}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-slate-700 capitalize">{factor.replace(/_/g, ' ')}</span>
                      <span className="text-xs font-bold text-slate-400">{barWidth}%</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[#0F4C3A] transition-all duration-500"
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-slate-400 text-xs py-8 text-center">Run a check-in to see factors</p>
          )}
        </div>
      </div>

      {/* Recommendations */}
      <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#0F4C3A]" />
            Recommended Interventions
            {recommendations?.total_recommendations != null && (
              <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold rounded-full px-2.5 py-0.5">{recommendations.total_recommendations}</span>
            )}
          </h2>
          <span className="text-xs text-slate-400 font-medium">Rules: {recommendations?.rules_config_source}</span>
        </div>

        {!recommendations?.interventions?.length ? (
          <p className="text-slate-400 text-xs text-center py-8">No interventions triggered at current risk level</p>
        ) : (
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            {recommendations.interventions.map((item, i) => {
              const Icon = CATEGORY_ICONS[item.category] || Shield;
              const colorClass = CATEGORY_COLORS[item.category] || 'border-slate-200 bg-slate-50 text-slate-800';
              return (
                <div
                  key={i}
                  className={`border rounded-2xl p-5 ${colorClass} flex flex-col gap-2 shadow-2xs`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 flex-shrink-0" />
                      <span className="text-xs font-bold uppercase tracking-wider opacity-90">{item.category?.replace(/_/g, ' ')}</span>
                    </div>
                    <span className={`text-[10px] border rounded-full px-2.5 py-0.5 font-bold uppercase tracking-wider flex-shrink-0 ${PRIORITY_BADGE[item.priority] || PRIORITY_BADGE.routine}`}>
                      {item.priority}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 leading-snug">{item.title}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed font-medium">{item.description}</p>
                  <div className="mt-auto pt-2 border-t border-slate-200/50">
                    <p className="text-[11px] text-slate-500 font-medium">{item.recommended_authority}</p>
                  </div>
                  {item.reason && (
                    <details className="mt-1">
                      <summary className="text-[11px] text-slate-500 font-bold cursor-pointer hover:underline">Why this? ↓</summary>
                      <p className="text-[11px] text-slate-600 mt-1 leading-relaxed bg-white/70 p-2 rounded-xl">{item.reason}</p>
                    </details>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Recent Check-Ins Table */}
      <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-400" />
          Recent Check-Ins
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="text-slate-400 border-b border-slate-100 uppercase tracking-wider font-semibold">
                {['Date', 'Channel', 'Sentiment', 'Emotion', 'Distress Score', 'Engagement'].map((h) => (
                  <th key={h} className="py-3 px-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {checkIns.slice(0, 10).map((ci) => (
                <tr key={ci.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-3 text-slate-500 font-medium">{ci.timestamp ? format(parseISO(ci.timestamp), 'dd MMM HH:mm') : '—'}</td>
                  <td className="py-3 px-3 capitalize font-bold text-slate-800">{ci.channel}</td>
                  <td className="py-3 px-3">
                    <span className={`font-bold ${ci.sentiment_score < -0.2 ? 'text-rose-600' : ci.sentiment_score > 0.2 ? 'text-emerald-700' : 'text-slate-500'}`}>
                      {ci.sentiment_score?.toFixed(2) ?? '—'}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-700 capitalize font-medium">{ci.emotion_label || '—'}</td>
                  <td className="py-3 px-3"><DistressScore score={ci.distress_score ?? 0} /></td>
                  <td className="py-3 px-3 text-slate-600 font-medium">{ci.engagement_score != null ? `${(ci.engagement_score * 100).toFixed(0)}%` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
