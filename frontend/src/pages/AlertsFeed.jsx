import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchAlerts, updateAlert } from '../api/client';
import { RiskBadge, Spinner } from '../components/ui';
import {
  Bell, RefreshCw, CheckCheck, UserPlus, AlertTriangle, Clock,
  ChevronRight, Loader2, Filter, ShieldAlert
} from 'lucide-react';
import { parseISO, formatDistanceToNow } from 'date-fns';

const STATUS_STYLES = {
  open: 'bg-rose-50 text-rose-700 border border-rose-200',
  assigned: 'bg-amber-50 text-amber-700 border border-amber-200',
  resolved: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
  escalated: 'bg-purple-50 text-purple-700 border border-purple-200',
};

function AlertCard({ alert, onAssign, onResolve, loading }) {
  const navigate = useNavigate();

  return (
    <div className={`p-6 rounded-3xl bg-white border transition-all duration-200 shadow-sm hover:shadow-md ${
      alert.status === 'open' ? 'border-rose-200 ring-1 ring-rose-100' : 'border-slate-100'
    }`}>
      <div className="flex items-start justify-between gap-3">
        {/* Left: Risk + ID */}
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full flex-shrink-0 ${
            alert.risk_level === 'critical' ? 'bg-rose-500 animate-pulse' :
            alert.risk_level === 'high' ? 'bg-amber-500' :
            'bg-emerald-500'
          }`} />
          <div>
            <div className="flex items-center gap-2 mb-1">
              <RiskBadge level={alert.risk_level} />
              <span
                className="text-[#0F4C3A] font-mono text-xs font-bold cursor-pointer hover:underline transition"
                onClick={() => navigate(`/victims/${alert.victim_id}`)}
              >
                {alert.victim_id}
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-1 font-medium">
              <Clock className="w-3 h-3" />
              {alert.triggered_at ? formatDistanceToNow(parseISO(alert.triggered_at), { addSuffix: true }) : '—'}
            </p>
          </div>
        </div>

        {/* Right: Status */}
        <span className={`text-[11px] px-3 py-1 rounded-full font-bold uppercase tracking-wider ${STATUS_STYLES[alert.status] || STATUS_STYLES.open}`}>
          {alert.status}
        </span>
      </div>

      {/* Metadata */}
      <div className="mt-4 grid grid-cols-2 gap-2.5 text-xs">
        {alert.distress_score != null && (
          <div className="bg-slate-50 border border-slate-100 rounded-2xl px-3.5 py-2.5">
            <p className="text-slate-400 text-[11px] font-medium mb-0.5">Distress Score</p>
            <p className="text-slate-900 font-extrabold text-base tabular-nums">{alert.distress_score?.toFixed(1)}</p>
          </div>
        )}
        {alert.escalation_probability != null && (
          <div className="bg-slate-50 border border-slate-100 rounded-2xl px-3.5 py-2.5">
            <p className="text-slate-400 text-[11px] font-medium mb-0.5">Escalation Prob.</p>
            <p className="text-slate-900 font-extrabold text-base tabular-nums">{(alert.escalation_probability * 100).toFixed(0)}%</p>
          </div>
        )}
      </div>

      {alert.assigned_to && (
        <p className="mt-3 text-xs text-slate-500 font-medium">
          Assigned to: <span className="text-slate-800 font-bold">{alert.assigned_to}</span>
        </p>
      )}

      {/* Actions */}
      {alert.status === 'open' && (
        <div className="mt-5 flex gap-2.5">
          <button
            onClick={() => onAssign(alert.id)}
            disabled={loading === alert.id}
            className="flex-1 flex items-center justify-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-full py-2.5 transition-all disabled:opacity-50 cursor-pointer active:scale-95"
          >
            {loading === alert.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <UserPlus className="w-3.5 h-3.5" />}
            Assign Counsellor
          </button>
          <button
            onClick={() => onResolve(alert.id)}
            disabled={loading === alert.id}
            className="flex-1 flex items-center justify-center gap-1.5 bg-[#0F4C3A] hover:bg-[#0A392B] text-white text-xs font-bold rounded-full py-2.5 transition-all shadow-xs disabled:opacity-50 cursor-pointer active:scale-95"
          >
            <CheckCheck className="w-3.5 h-3.5" />
            Resolve
          </button>
        </div>
      )}
      {alert.status === 'assigned' && (
        <button
          onClick={() => onResolve(alert.id)}
          disabled={loading === alert.id}
          className="mt-5 w-full flex items-center justify-center gap-1.5 bg-[#0F4C3A] hover:bg-[#0A392B] text-white text-xs font-bold rounded-full py-2.5 transition-all shadow-xs disabled:opacity-50 cursor-pointer active:scale-95"
        >
          <CheckCheck className="w-3.5 h-3.5" />
          Mark Resolved
        </button>
      )}
    </div>
  );
}

export default function AlertsFeed() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');
  const intervalRef = useRef(null);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await fetchAlerts({ limit: 50 });
      setAlerts(data?.alerts || data || []);
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    intervalRef.current = setInterval(() => load(true), 30000);
    return () => clearInterval(intervalRef.current);
  }, [load]);

  const handleAssign = async (id) => {
    setActionLoading(id);
    try {
      await updateAlert(id, { status: 'assigned', assigned_to: 'counsellor_anjali' });
      await load(true);
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResolve = async (id) => {
    setActionLoading(id);
    try {
      await updateAlert(id, { status: 'resolved' });
      await load(true);
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(null);
    }
  };

  const filtered = alerts.filter((a) => {
    if (statusFilter !== 'all' && a.status !== statusFilter) return false;
    if (riskFilter !== 'all' && a.risk_level !== riskFilter) return false;
    return true;
  });

  const openCount = alerts.filter((a) => a.status === 'open').length;

  return (
    <div className="max-w-6xl mx-auto space-y-7 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
            Alerts Feed
            {openCount > 0 && (
              <span className="flex items-center justify-center w-6 h-6 bg-rose-600 text-white text-xs font-extrabold rounded-full">
                {openCount}
              </span>
            )}
          </h1>
          <p className="text-slate-500 text-sm mt-1 font-medium">Real-time distress warning engine · Action required to close</p>
        </div>
        <button
          onClick={() => load()}
          className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold border border-slate-200 shadow-2xs transition-all active:scale-95 cursor-pointer self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Open Alerts', count: alerts.filter(a => a.status === 'open').length, color: 'text-rose-600', bg: 'bg-rose-50 border-rose-200' },
          { label: 'Assigned', count: alerts.filter(a => a.status === 'assigned').length, color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200' },
          { label: 'Resolved', count: alerts.filter(a => a.status === 'resolved').length, color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' },
        ].map(({ label, count, color, bg }) => (
          <div key={label} className={`p-5 rounded-3xl bg-white border border-slate-100 shadow-sm flex items-center justify-between`}>
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{label}</p>
              <h3 className={`text-3xl font-extrabold mt-1 tabular-nums ${color}`}>{count}</h3>
            </div>
            <div className={`w-10 h-10 rounded-2xl border flex items-center justify-center font-bold ${bg}`}>
              <ShieldAlert className={`w-5 h-5 ${color}`} />
            </div>
          </div>
        ))}
      </div>

      {/* Filters Bar */}
      <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-wrap gap-3 items-center">
        <Filter className="w-4 h-4 text-slate-400 ml-2" />
        <select
          className="bg-slate-50 text-slate-800 text-xs font-semibold px-4 py-2 rounded-full border border-slate-200 focus:outline-none focus:border-[#0F4C3A]"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Status</option>
          <option value="open">Open</option>
          <option value="assigned">Assigned</option>
          <option value="resolved">Resolved</option>
        </select>
        <select
          className="bg-slate-50 text-slate-800 text-xs font-semibold px-4 py-2 rounded-full border border-slate-200 focus:outline-none focus:border-[#0F4C3A]"
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
        >
          <option value="all">All Risk Levels</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="moderate">Moderate</option>
        </select>
        <span className="text-xs text-slate-400 font-semibold ml-auto mr-2">
          {filtered.length} alert{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Alert Cards Grid */}
      {loading ? (
        <Spinner />
      ) : error ? (
        <div className="text-rose-600 text-sm p-6 rounded-3xl bg-white border border-rose-200 text-center font-semibold">{error}</div>
      ) : filtered.length === 0 ? (
        <div className="p-16 rounded-3xl bg-white border border-slate-100 text-center shadow-sm">
          <Bell className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 font-semibold text-sm">No alerts match current filters</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-5">
          {filtered.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAssign={handleAssign}
              onResolve={handleResolve}
              loading={actionLoading}
            />
          ))}
        </div>
      )}
    </div>
  );
}
