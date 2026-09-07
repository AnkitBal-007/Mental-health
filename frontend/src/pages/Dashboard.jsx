import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { fetchVictims, fetchDashboardSummary } from '../api/client';
import { DistressScore, RiskBadge, TrendArrow, Spinner, EmptyState } from '../components/ui';
import {
  ArrowUpRight, Plus, Video, Play, Pause, Square, Search,
  ChevronUp, ChevronDown, RefreshCw, Users, ShieldAlert,
  Calendar, CheckCircle2, Clock, Sparkles, Filter, ChevronRight
} from 'lucide-react';
import { format } from 'date-fns';

const RISK_ORDER = { critical: 4, high: 3, moderate: 2, low: 1 };

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [victims, setVictims] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Live Timer for Time Tracker widget
  const [timerSeconds, setTimerSeconds] = useState(5048); // 01:24:08 initial
  const [timerRunning, setTimerRunning] = useState(true);

  // Table filters & sort
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  const [districtFilter, setDistrictFilter] = useState('all');
  const [sortField, setSortField] = useState('current_distress_score');
  const [sortDir, setSortDir] = useState('desc');

  // Active chart day hover
  const [activeDayIndex, setActiveDayIndex] = useState(3); // Wednesday (74%)

  useEffect(() => {
    let interval = null;
    if (timerRunning) {
      interval = setInterval(() => {
        setTimerSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [timerRunning]);

  const formatTimer = (totalSeconds) => {
    const hrs = Math.floor(totalSeconds / 3600).toString().padStart(2, '0');
    const mins = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, '0');
    const secs = (totalSeconds % 60).toString().padStart(2, '0');
    return `${hrs}:${mins}:${secs}`;
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchVictims({ limit: 100 });
      setVictims(data?.victims || data || []);

      const scope = user?.role === 'national' ? 'national' : user?.role === 'state' ? 'state' : 'district';
      const scopeId = user?.district || user?.state || 'national';
      const sum = await fetchDashboardSummary(scope, scopeId);
      setSummary(sum);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => { load(); }, [load]);

  const districts = [...new Set(victims.map((v) => v.assigned_district).filter(Boolean))];

  const filtered = victims
    .filter((v) => {
      if (riskFilter !== 'all' && v.risk_level?.toLowerCase() !== riskFilter) return false;
      if (districtFilter !== 'all' && v.assigned_district !== districtFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          v.id?.toLowerCase().includes(q) ||
          v.case_type?.toLowerCase().includes(q) ||
          v.full_name?.toLowerCase().includes(q)
        );
      }
      return true;
    })
    .sort((a, b) => {
      let av = a[sortField], bv = b[sortField];
      if (sortField === 'risk_level') {
        av = RISK_ORDER[a.risk_level?.toLowerCase()] || 0;
        bv = RISK_ORDER[b.risk_level?.toLowerCase()] || 0;
      }
      if (av == null) return 1;
      if (bv == null) return -1;
      return sortDir === 'desc' ? (bv > av ? 1 : -1) : (av > bv ? 1 : -1);
    });

  const toggleSort = (field) => {
    if (sortField === field) setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    else { setSortField(field); setSortDir('desc'); }
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ChevronUp className="w-3 h-3 text-slate-400" />;
    return sortDir === 'desc'
      ? <ChevronDown className="w-3 h-3 text-[#0F4C3A]" />
      : <ChevronUp className="w-3 h-3 text-[#0F4C3A]" />;
  };

  // Metrics calculation
  const totalCount = summary?.total_victims ?? (victims.length || 24);
  const resolvedCount = victims.filter(v => v.trajectory === 'recovery' || v.risk_level === 'low').length || 10;
  const runningCount = victims.filter(v => ['moderate', 'high'].includes(v.risk_level)).length || 12;
  const pendingAlertsCount = summary?.active_alerts ?? (victims.filter(v => v.risk_level === 'critical').length || 2);

  // Weekly analytics capsule bar data
  const chartDays = [
    { day: 'S', height: 'h-24', isPattern: true, pct: '35%' },
    { day: 'M', height: 'h-32', isPattern: true, pct: '48%' },
    { day: 'T', height: 'h-36', isSolid: true, bg: 'bg-[#10B981]', pct: '74%', showTooltip: true },
    { day: 'W', height: 'h-40', isSolid: true, bg: 'bg-[#0F4C3A]', pct: '88%' },
    { day: 'T', height: 'h-32', isPattern: true, pct: '52%' },
    { day: 'F', height: 'h-36', isPattern: true, pct: '60%' },
    { day: 'S', height: 'h-28', isPattern: true, pct: '42%' },
  ];

  // Team collaboration items with clean initials avatar badges
  const teamMembers = [
    { name: 'Alexandra Deff', initials: 'AD', bg: 'bg-rose-100 text-rose-700', task: 'Case VIC-2024-10001 Intake Assessment', status: 'Completed' },
    { name: 'Edwin Adenike', initials: 'EA', bg: 'bg-emerald-100 text-emerald-800', task: 'Intimidation Threat Log Analysis', status: 'In Progress' },
    { name: 'Isaac Oluwatemilorun', initials: 'IO', bg: 'bg-blue-100 text-blue-800', task: 'Psychological Crisis Evaluation', status: 'Pending' },
    { name: 'David Oshodi', initials: 'DO', bg: 'bg-amber-100 text-amber-800', task: 'Court Witness Protection Protocol', status: 'In Progress' },
  ];

  // Priority case feed with clean Donezo-style vector shapes
  const priorityCases = [
    {
      id: 'VIC-2024-10003',
      title: 'Develop API Endpoints',
      due: 'Due date: Nov 26, 2024',
      icon: (
        <svg className="w-5 h-5 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
          <rect x="5" y="4" width="3.5" height="16" rx="1.75" transform="rotate(25 6.75 12)" />
          <rect x="13" y="4" width="3.5" height="16" rx="1.75" transform="rotate(25 14.75 12)" />
        </svg>
      ),
      iconBg: 'bg-blue-50',
    },
    {
      id: 'VIC-2024-10002',
      title: 'Onboarding Flow',
      due: 'Due date: Nov 28, 2024',
      icon: (
        <svg className="w-5 h-5 text-emerald-600" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="7" r="3" />
          <path d="M6 18c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none" />
        </svg>
      ),
      iconBg: 'bg-emerald-50',
    },
    {
      id: 'VIC-2024-10005',
      title: 'Build Dashboard',
      due: 'Due date: Nov 30, 2024',
      icon: (
        <svg className="w-5 h-5" viewBox="0 0 24 24">
          <circle cx="8" cy="8" r="3" fill="#84cc16" />
          <circle cx="16" cy="8" r="3" fill="#06b6d4" />
          <circle cx="8" cy="16" r="3" fill="#f59e0b" />
          <circle cx="16" cy="16" r="3" fill="#ec4899" />
        </svg>
      ),
      iconBg: 'bg-slate-50',
    },
    {
      id: 'VIC-2024-10006',
      title: 'Optimize Page Load',
      due: 'Due date: Dec 5, 2024',
      icon: (
        <svg className="w-5 h-5 text-amber-500" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3a9 9 0 0 0-9 9h9V3z" opacity="0.4" />
          <path d="M12 3v9h9a9 9 0 0 0-9-9z" />
          <path d="M12 12v9a9 9 0 0 0 9-9h-9z" opacity="0.7" />
        </svg>
      ),
      iconBg: 'bg-amber-50',
    },
    {
      id: 'VIC-2024-10001',
      title: 'Cross-Browser Testing',
      due: 'Due date: Dec 6, 2024',
      icon: (
        <svg className="w-5 h-5 text-purple-600" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="7" r="3" />
          <circle cx="7" cy="16" r="3" />
          <circle cx="17" cy="16" r="3" />
        </svg>
      ),
      iconBg: 'bg-purple-50',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-7 pb-12">
      {/* ── Page Header & Action Controls ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Dashboard</h2>
          <p className="text-sm text-slate-500 mt-1 font-medium">
            Plan, prioritize, and monitor victim distress cases with ease.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/alerts')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#0F4C3A] hover:bg-[#0A392B] text-white text-sm font-semibold shadow-sm transition-all active:scale-95 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Add Case</span>
          </button>

          <button
            onClick={() => navigate('/simulation')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold border border-slate-200 shadow-2xs transition-all active:scale-95 cursor-pointer"
          >
            <span>Import Data</span>
          </button>
        </div>
      </div>

      {/* ── Top Metric Cards (4 Columns) ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Total Cases (Highlighted Dark Emerald Gradient) */}
        <div className="p-6 rounded-3xl bg-gradient-to-br from-[#0F4C3A] via-[#0C3F30] to-[#07281F] text-white shadow-sm flex flex-col justify-between relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-emerald-100/90">Total Cases</span>
            <div className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
              <ArrowUpRight className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="my-3">
            <h3 className="text-4xl font-extrabold text-white tracking-tight">{totalCount}</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 bg-emerald-500/20 text-emerald-200 border border-emerald-400/20 px-2.5 py-0.5 rounded-full text-xs font-semibold">
              <span className="text-[10px]">↗</span> 5%
            </span>
            <span className="text-xs text-emerald-100/70 font-medium">Increased from last month</span>
          </div>
        </div>

        {/* Card 2: Ended / Resolved Cases */}
        <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-600">Resolved Cases</span>
            <div className="w-8 h-8 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center">
              <ArrowUpRight className="w-4 h-4 text-slate-600" />
            </div>
          </div>
          <div className="my-3">
            <h3 className="text-4xl font-extrabold text-slate-900 tracking-tight">{resolvedCount}</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full text-xs font-semibold">
              <span className="text-[10px]">↗</span> 6%
            </span>
            <span className="text-xs text-slate-400 font-medium">Increased from last month</span>
          </div>
        </div>

        {/* Card 3: Active / Running Cases */}
        <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-600">Active Monitoring</span>
            <div className="w-8 h-8 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center">
              <ArrowUpRight className="w-4 h-4 text-slate-600" />
            </div>
          </div>
          <div className="my-3">
            <h3 className="text-4xl font-extrabold text-slate-900 tracking-tight">{runningCount}</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full text-xs font-semibold">
              <span className="text-[10px]">↗</span> 2
            </span>
            <span className="text-xs text-slate-400 font-medium">Increased from last month</span>
          </div>
        </div>

        {/* Card 4: Pending Alerts */}
        <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-600">Pending Alerts</span>
            <div className="w-8 h-8 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center">
              <ArrowUpRight className="w-4 h-4 text-slate-600" />
            </div>
          </div>
          <div className="my-3">
            <h3 className="text-4xl font-extrabold text-slate-900 tracking-tight">{pendingAlertsCount}</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full text-xs font-semibold">
              On Discuss
            </span>
            <span className="text-xs text-slate-400 font-medium">Immediate triage</span>
          </div>
        </div>
      </div>

      {/* ── Middle Grid: Analytics Chart + Reminders + Priority Cases ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Widget 1: Case Analytics Capsule Chart (5 cols) */}
        <div className="lg:col-span-4 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <h4 className="text-base font-bold text-slate-900">Case Analytics</h4>
            <p className="text-xs text-slate-400 mt-0.5">Weekly check-in volume & distress levels</p>
          </div>

          {/* Capsule Pill Bars */}
          <div className="pt-8 pb-3 px-2 flex items-end justify-between gap-2 h-52">
            {chartDays.map((item, idx) => (
              <div key={idx} className="flex flex-col items-center gap-2 flex-1 relative group cursor-pointer">
                {/* Floating Tooltip Pill */}
                {item.showTooltip && (
                  <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-white border border-slate-200 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-md shadow-sm pointer-events-none">
                    {item.pct}
                  </div>
                )}

                <div
                  className={`w-full ${item.height} rounded-full transition-all duration-300 ${
                    item.isSolid
                      ? item.bg
                      : 'stripe-pattern border border-slate-200'
                  } group-hover:opacity-90 group-hover:scale-105`}
                />
                <span className="text-xs font-semibold text-slate-400">{item.day}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Widget 2: Reminders Card (4 cols) */}
        <div className="lg:col-span-4 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Reminders</span>
            <h4 className="text-lg font-bold text-slate-900 mt-3 leading-snug">
              Multi-Disciplinary Case Review & Psychological Support
            </h4>
            <p className="text-xs text-slate-400 mt-2 font-medium">
              Time: 02.00 pm - 04.00 pm
            </p>
          </div>

          <div className="pt-6">
            <button
              onClick={() => alert("Launching Secure Tele-Consultation Room for Patna Case Review...")}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-2xl bg-[#0F4C3A] hover:bg-[#0A392B] text-white text-sm font-semibold shadow-sm transition-all active:scale-95 cursor-pointer"
            >
              <Video className="w-4 h-4 text-emerald-200" />
              <span>Start Review Session</span>
            </button>
          </div>
        </div>

        {/* Widget 3: Priority Case Queue (4 cols) */}
        <div className="lg:col-span-4 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-base font-bold text-slate-900">Priority Cases</h4>
            <button
              onClick={() => navigate('/alerts')}
              className="text-xs font-semibold text-slate-700 hover:text-slate-900 border border-slate-200 rounded-full px-3 py-1 bg-white hover:bg-slate-50 transition-colors cursor-pointer"
            >
              + New
            </button>
          </div>

          <div className="space-y-2.5">
            {priorityCases.map((c, i) => (
              <div
                key={i}
                onClick={() => navigate(`/victims/${c.id}`)}
                className="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer group"
              >
                <div className={`w-8 h-8 rounded-xl ${c.iconBg} flex items-center justify-center flex-shrink-0`}>
                  {c.icon}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-slate-800 truncate group-hover:text-[#0F4C3A]">
                    {c.title}
                  </p>
                  <p className="text-[11px] text-slate-400">{c.due}</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Lower Grid: Team Collaboration + Progress Gauge + Time Tracker ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Widget 4: Team Collaboration (5 cols) */}
        <div className="lg:col-span-5 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-base font-bold text-slate-900">Team Collaboration</h4>
              <p className="text-xs text-slate-400">Assigned counsellors & protection officers</p>
            </div>
            <button
              onClick={() => alert("Add Counsellor dialog")}
              className="text-xs font-semibold text-slate-700 hover:text-slate-900 border border-slate-200 rounded-full px-3 py-1 bg-white hover:bg-slate-50 transition-colors cursor-pointer"
            >
              + Add Member
            </button>
          </div>

          <div className="space-y-3">
            {teamMembers.map((m, i) => (
              <div key={i} className="flex items-center justify-between gap-3 p-2 rounded-xl hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-9 h-9 rounded-full ${m.bg} flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-2xs`}>
                    {m.initials}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-slate-900 truncate">{m.name}</p>
                    <p className="text-[11px] text-slate-400 truncate">{m.task}</p>
                  </div>
                </div>

                <span
                  className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full flex-shrink-0 ${
                    m.status === 'Completed'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : m.status === 'In Progress'
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-rose-50 text-rose-700 border border-rose-200'
                  }`}
                >
                  {m.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Widget 5: Case Progress Semi-Circle Arc (4 cols) */}
        <div className="lg:col-span-4 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <h4 className="text-base font-bold text-slate-900">Distress Resolution</h4>
            <p className="text-xs text-slate-400">Longitudinal recovery & stabilization</p>
          </div>

          {/* Radial Arc SVG Gauge */}
          <div className="flex flex-col items-center justify-center py-4 relative">
            <svg className="w-44 h-24 overflow-visible" viewBox="0 0 160 80">
              {/* Background Arc Track */}
              <path
                d="M 15 80 A 65 65 0 0 1 145 80"
                fill="none"
                stroke="#E2E8F0"
                strokeWidth="18"
                strokeLinecap="round"
              />
              {/* Foreground Emerald Arc */}
              <path
                d="M 15 80 A 65 65 0 0 1 115 25"
                fill="none"
                stroke="#0F4C3A"
                strokeWidth="18"
                strokeLinecap="round"
              />
            </svg>

            {/* Centered Percentage Stat */}
            <div className="text-center mt-2">
              <span className="text-3xl font-extrabold text-slate-900 tracking-tight">68%</span>
              <p className="text-xs text-slate-400 font-medium">Cases Stabilized</p>
            </div>
          </div>

          {/* Legend Chips */}
          <div className="flex items-center justify-center gap-4 pt-2 border-t border-slate-100 text-xs text-slate-500 font-medium">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0F4C3A]" /> Stabilized
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" /> In Progress
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-300" /> Pending
            </span>
          </div>
        </div>

        {/* Widget 6: Time Tracker / Active Triage Hotline (3 cols) */}
        <div className="lg:col-span-3 p-6 rounded-3xl bg-[#082E23] text-white shadow-sm flex flex-col justify-between relative overflow-hidden">
          {/* Subtle wavy topographical overlay */}
          <div className="absolute inset-0 opacity-15 pointer-events-none bg-[radial-gradient(#10B981_1px,transparent_1px)] [background-size:16px_16px]" />

          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-300 uppercase tracking-wider">Triage Live Monitor</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <p className="text-xs text-emerald-200/70 mt-1">Active case triage session</p>
          </div>

          {/* Digital Timer */}
          <div className="my-6 text-center">
            <span className="text-3xl sm:text-4xl font-extrabold tracking-widest font-mono text-white">
              {formatTimer(timerSeconds)}
            </span>
          </div>

          {/* Control Buttons */}
          <div className="flex items-center justify-center gap-4 pt-2">
            <button
              onClick={() => setTimerRunning(!timerRunning)}
              className="w-11 h-11 rounded-full bg-white text-slate-900 hover:bg-emerald-50 flex items-center justify-center shadow-sm transition-transform active:scale-90 cursor-pointer"
              title={timerRunning ? "Pause" : "Play"}
            >
              {timerRunning ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
            </button>

            <button
              onClick={() => { setTimerRunning(false); setTimerSeconds(0); }}
              className="w-11 h-11 rounded-full bg-rose-600 hover:bg-rose-500 text-white flex items-center justify-center shadow-sm transition-transform active:scale-90 cursor-pointer"
              title="Stop & Log Session"
            >
              <Square className="w-4 h-4 fill-current" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Full Interactive Victim Registry Table ── */}
      <div className="rounded-3xl bg-white border border-slate-100 shadow-sm p-6">
        {/* Table Header & Search Filter Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Registered Victim Cases</h3>
            <p className="text-xs text-slate-400">Jurisdictionally anonymized longitudinal distress tracking</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter by ID or Case Type..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="bg-slate-50 text-slate-800 placeholder-slate-400 text-xs pl-9 pr-3 py-2 rounded-full border border-slate-200 focus:outline-none focus:border-[#0F4C3A]"
              />
            </div>

            {/* Risk Filter Select */}
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-slate-50 text-slate-700 text-xs font-semibold px-3 py-2 rounded-full border border-slate-200 focus:outline-none focus:border-[#0F4C3A]"
            >
              <option value="all">All Risk Levels</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="moderate">Moderate</option>
              <option value="low">Low</option>
            </select>

            {/* Refresh Button */}
            <button
              onClick={load}
              className="w-9 h-9 rounded-full bg-slate-50 hover:bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 transition-colors cursor-pointer"
              title="Refresh Cases"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Table Body */}
        {loading ? (
          <Spinner />
        ) : error ? (
          <div className="py-8 text-center text-rose-600 text-sm font-semibold">{error}</div>
        ) : filtered.length === 0 ? (
          <EmptyState message="No matching victim cases found in jurisdiction." />
        ) : (
          <div className="overflow-x-auto mt-2">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3.5 px-3">Victim ID</th>
                  <th className="py-3.5 px-3">Case Type</th>
                  <th className="py-3.5 px-3">District</th>
                  <th className="py-3.5 px-3 cursor-pointer select-none" onClick={() => toggleSort('risk_level')}>
                    <div className="flex items-center gap-1">Risk Level <SortIcon field="risk_level" /></div>
                  </th>
                  <th className="py-3.5 px-3 cursor-pointer select-none" onClick={() => toggleSort('current_distress_score')}>
                    <div className="flex items-center gap-1">Distress Score <SortIcon field="current_distress_score" /></div>
                  </th>
                  <th className="py-3.5 px-3">Trend</th>
                  <th className="py-3.5 px-3">Escalation Prob</th>
                  <th className="py-3.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filtered.map((v) => (
                  <tr
                    key={v.id}
                    onClick={() => navigate(`/victims/${v.id}`)}
                    className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                  >
                    <td className="py-3.5 px-3 font-mono font-bold text-slate-900 group-hover:text-[#0F4C3A]">
                      {v.id}
                    </td>
                    <td className="py-3.5 px-3 text-slate-600 font-medium">
                      {v.case_type || 'SC/ST Protection'}
                    </td>
                    <td className="py-3.5 px-3 text-slate-600">
                      {v.assigned_district || 'Patna'}
                    </td>
                    <td className="py-3.5 px-3">
                      <RiskBadge level={v.risk_level} />
                    </td>
                    <td className="py-3.5 px-3">
                      <DistressScore score={v.current_distress_score} />
                    </td>
                    <td className="py-3.5 px-3">
                      <TrendArrow trend={v.distress_trend} />
                    </td>
                    <td className="py-3.5 px-3 font-semibold text-slate-700">
                      {v.escalation_probability != null ? `${(v.escalation_probability * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td className="py-3.5 px-3 text-right">
                      <span className="inline-flex items-center gap-1 text-slate-400 group-hover:text-[#0F4C3A] font-semibold">
                        View <ChevronRight className="w-3.5 h-3.5" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
