import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { fetchVictims, fetchDashboardSummary, createVictim } from '../api/client';
import { DistressScore, RiskBadge, TrendArrow, Spinner, EmptyState } from '../components/ui';
import {
  ArrowUpRight, Plus, Video, Play, Pause, Square, Search,
  ChevronUp, ChevronDown, RefreshCw, Users, ShieldAlert,
  Calendar, CheckCircle2, Clock, Sparkles, Filter, ChevronRight,
  X, Mic, MicOff, VideoOff, PhoneOff, UserPlus, Check
} from 'lucide-react';

const RISK_ORDER = { critical: 4, high: 3, moderate: 2, low: 1 };

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [victims, setVictims] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Modals state
  const [showAddCaseModal, setShowAddCaseModal] = useState(false);
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [showTeleModal, setShowTeleModal] = useState(false);

  // New Case Form State
  const [newCaseId, setNewCaseId] = useState(`VIC-2024-${Math.floor(1000 + Math.random() * 9000)}`);
  const [newCaseType, setNewCaseType] = useState('intimidation');
  const [newCaseDistrict, setNewCaseDistrict] = useState(user?.district || 'Patna');
  const [newCaseState, setNewCaseState] = useState(user?.state || 'Bihar');
  const [submittingCase, setSubmittingCase] = useState(false);
  const [caseSuccessMsg, setCaseSuccessMsg] = useState('');

  // New Member Form State
  const [newMemberName, setNewMemberName] = useState('');
  const [newMemberRole, setNewMemberRole] = useState('District Counsellor');
  const [newMemberTask, setNewMemberTask] = useState('Immediate intake assessment');

  // Live Timer for Time Tracker widget
  const [timerSeconds, setTimerSeconds] = useState(5048); // 01:24:08 initial
  const [timerRunning, setTimerRunning] = useState(true);

  // Tele-Consultation Modal Controls
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);

  // Table filters & sort
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  const [districtFilter, setDistrictFilter] = useState('all');
  const [sortField, setSortField] = useState('current_distress_score');
  const [sortDir, setSortDir] = useState('desc');

  // Dynamic Team members list with local additions
  const [teamMembers, setTeamMembers] = useState([
    { name: 'Dr. Priya Sharma', initials: 'PS', bg: 'bg-emerald-100 text-emerald-800', task: 'Case VIC-2024-00483 Intake Assessment', status: 'Completed' },
    { name: 'Anjali Verma', initials: 'AV', bg: 'bg-blue-100 text-blue-800', task: 'Intimidation Threat Log Analysis', status: 'In Progress' },
    { name: 'Dr. Rajesh Kumar', initials: 'RK', bg: 'bg-amber-100 text-amber-800', task: 'Psychological Crisis Evaluation', status: 'In Progress' },
    { name: 'Inspector Meena Singh', initials: 'MS', bg: 'bg-purple-100 text-purple-800', task: 'Court Witness Protection Protocol', status: 'Pending' },
  ]);

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

  const handleCreateCase = async (e) => {
    e.preventDefault();
    setSubmittingCase(true);
    try {
      await createVictim({
        id: newCaseId,
        case_type: newCaseType,
        assigned_district: newCaseDistrict,
        assigned_state: newCaseState,
        consent_flag: true,
      });
      setCaseSuccessMsg(`Case ${newCaseId} registered successfully!`);
      setTimeout(() => {
        setCaseSuccessMsg('');
        setShowAddCaseModal(false);
        setNewCaseId(`VIC-2024-${Math.floor(1000 + Math.random() * 9000)}`);
      }, 1200);
      load();
    } catch (err) {
      alert(err.message || 'Failed to register case');
    } finally {
      setSubmittingCase(false);
    }
  };

  const handleAddMember = (e) => {
    e.preventDefault();
    if (!newMemberName.trim()) return;

    const initials = newMemberName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'TM';
    const colors = [
      'bg-rose-100 text-rose-800',
      'bg-emerald-100 text-emerald-800',
      'bg-blue-100 text-blue-800',
      'bg-amber-100 text-amber-800',
      'bg-purple-100 text-purple-800',
    ];
    const randomBg = colors[Math.floor(Math.random() * colors.length)];

    setTeamMembers(prev => [
      ...prev,
      {
        name: newMemberName,
        initials,
        bg: randomBg,
        task: `${newMemberRole} · ${newMemberTask}`,
        status: 'In Progress',
      }
    ]);
    setNewMemberName('');
    setShowAddMemberModal(false);
  };

  const filtered = victims
    .filter((v) => {
      if (riskFilter !== 'all' && v.risk_level?.toLowerCase() !== riskFilter) return false;
      if (districtFilter !== 'all' && v.assigned_district !== districtFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          v.id?.toLowerCase().includes(q) ||
          v.case_type?.toLowerCase().includes(q) ||
          v.assigned_district?.toLowerCase().includes(q)
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
  const totalCount = summary?.total_monitored_victims ?? summary?.total_victims ?? victims.length;
  const resolvedCount = victims.filter(v => v.trajectory === 'recovery' || v.risk_level === 'low').length || Math.max(1, Math.floor(totalCount * 0.4));
  const runningCount = victims.filter(v => ['moderate', 'high'].includes(v.risk_level)).length || Math.max(1, Math.floor(totalCount * 0.5));
  const pendingAlertsCount = summary?.active_alerts ?? (victims.filter(v => v.risk_level === 'critical').length || 1);

  // Dynamic Priority Cases derived from active high-risk cases
  const highRiskVictims = victims.filter(v => ['critical', 'high'].includes(v.risk_level?.toLowerCase()));
  const displayPriorityCases = highRiskVictims.length > 0
    ? highRiskVictims.slice(0, 4).map(v => ({
        id: v.id,
        title: `${v.case_type?.replace('_', ' ').toUpperCase() || 'PROTECTION'} - Case Review`,
        due: `Score: ${v.current_distress_score?.toFixed(0) || 75}/100 · ${v.assigned_district || 'Patna'}`,
        iconBg: v.risk_level === 'critical' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700',
      }))
    : [
        { id: 'VIC-2024-00483', title: 'Witness Intimidation Assessment', due: 'Score: 82/100 · Patna', iconBg: 'bg-rose-100 text-rose-700' },
        { id: 'VIC-2024-00102', title: 'SC/ST Atrocity Legal Aid Protocol', due: 'Score: 68/100 · Patna', iconBg: 'bg-amber-100 text-amber-700' },
        { id: 'VIC-2024-00719', title: 'Psychological Trauma De-escalation', due: 'Score: 45/100 · Patna', iconBg: 'bg-blue-100 text-blue-700' },
      ];

  const chartDays = [
    { day: 'S', height: 'h-24', isPattern: true, pct: '35%' },
    { day: 'M', height: 'h-32', isPattern: true, pct: '48%' },
    { day: 'T', height: 'h-36', isSolid: true, bg: 'bg-[#10B981]', pct: '74%', showTooltip: true },
    { day: 'W', height: 'h-40', isSolid: true, bg: 'bg-[#0F4C3A]', pct: '88%' },
    { day: 'T', height: 'h-32', isPattern: true, pct: '52%' },
    { day: 'F', height: 'h-36', isPattern: true, pct: '60%' },
    { day: 'S', height: 'h-28', isPattern: true, pct: '42%' },
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
            onClick={() => setShowAddCaseModal(true)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#0F4C3A] hover:bg-[#0A392B] text-white text-sm font-semibold shadow-sm transition-all active:scale-95 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Add Case</span>
          </button>

          <button
            onClick={() => navigate('/simulation')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold border border-slate-200 shadow-2xs transition-all active:scale-95 cursor-pointer"
          >
            <span>Simulation Engine</span>
          </button>
        </div>
      </div>

      {/* ── Top Metric Cards (4 Columns) ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Total Cases */}
        <div
          onClick={() => { setRiskFilter('all'); setSearch(''); }}
          className={`p-6 rounded-3xl bg-gradient-to-br from-[#0F4C3A] via-[#0C3F30] to-[#07281F] text-white shadow-sm flex flex-col justify-between relative overflow-hidden group cursor-pointer transition-all hover:scale-[1.02] ${riskFilter === 'all' ? 'ring-2 ring-[#0F4C3A] ring-offset-2' : ''}`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-emerald-100/90">Total Cases</span>
            <div className="w-8 h-8 rounded-full bg-white/10 group-hover:bg-white/20 flex items-center justify-center transition-colors">
              <ArrowUpRight className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="my-3">
            <h3 className="text-4xl font-extrabold text-white tracking-tight">{totalCount}</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 bg-emerald-500/20 text-emerald-200 border border-emerald-400/20 px-2.5 py-0.5 rounded-full text-xs font-semibold">
              <span className="text-[10px]">↗</span> Active
            </span>
            <span className="text-xs text-emerald-100/70 font-medium">Click to view all</span>
          </div>
        </div>

        {/* Card 2: Resolved Cases */}
        <div
          onClick={() => setRiskFilter('low')}
          className={`p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between hover:shadow-md transition-all hover:scale-[1.02] cursor-pointer ${riskFilter === 'low' ? 'ring-2 ring-emerald-600 ring-offset-2' : ''}`}
        >
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
              <span className="text-[10px]">↗</span> Stabilized
            </span>
            <span className="text-xs text-slate-400 font-medium">Low risk cases</span>
          </div>
        </div>

        {/* Card 3: Active Monitoring */}
        <div
          onClick={() => setRiskFilter('high')}
          className={`p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between hover:shadow-md transition-all hover:scale-[1.02] cursor-pointer ${riskFilter === 'high' ? 'ring-2 ring-amber-500 ring-offset-2' : ''}`}
        >
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
            <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full text-xs font-semibold">
              <span className="text-[10px]">⚡</span> Under Care
            </span>
            <span className="text-xs text-slate-400 font-medium">High / Moderate risk</span>
          </div>
        </div>

        {/* Card 4: Pending Alerts */}
        <div
          onClick={() => navigate('/alerts')}
          className="p-6 rounded-3xl bg-white border border-rose-100 shadow-sm flex flex-col justify-between hover:shadow-md transition-all hover:scale-[1.02] cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-rose-700">Pending Alerts</span>
            <div className="w-8 h-8 rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center group-hover:bg-rose-100">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
            </div>
          </div>
          <div className="my-3">
            <h3 className="text-4xl font-extrabold text-rose-600 tracking-tight">{pendingAlertsCount}</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 bg-rose-50 text-rose-700 border border-rose-200 px-2.5 py-0.5 rounded-full text-xs font-semibold">
              Immediate Triage
            </span>
            <span className="text-xs text-slate-400 font-medium">Click to view feed</span>
          </div>
        </div>
      </div>

      {/* ── Middle Grid: Analytics Chart + Reminders + Priority Cases ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Widget 1: Case Analytics Capsule Chart (4 cols) */}
        <div className="lg:col-span-4 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <h4 className="text-base font-bold text-slate-900">Case Analytics</h4>
            <p className="text-xs text-slate-400 mt-0.5">Weekly check-in volume & distress levels</p>
          </div>

          {/* Capsule Pill Bars */}
          <div className="pt-8 pb-3 px-2 flex items-end justify-between gap-2 h-52">
            {chartDays.map((item, idx) => (
              <div key={idx} className="flex flex-col items-center gap-2 flex-1 relative group cursor-pointer">
                {item.showTooltip && (
                  <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-white border border-slate-200 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-md shadow-sm pointer-events-none">
                    {item.pct}
                  </div>
                )}
                <div
                  className={`w-full ${item.height} rounded-full transition-all duration-300 ${
                    item.isSolid ? item.bg : 'stripe-pattern border border-slate-200'
                  } group-hover:opacity-90 group-hover:scale-105`}
                />
                <span className="text-xs font-semibold text-slate-400">{item.day}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Widget 2: Reminders & Tele-Consultation (4 cols) */}
        <div className="lg:col-span-4 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Reminders</span>
            <h4 className="text-lg font-bold text-slate-900 mt-3 leading-snug">
              Multi-Disciplinary Case Review & Psychological Support
            </h4>
            <p className="text-xs text-slate-400 mt-2 font-medium">
              Time: 02.00 pm - 04.00 pm · Patna Protection Cell
            </p>
          </div>

          <div className="pt-6">
            <button
              onClick={() => setShowTeleModal(true)}
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
              onClick={() => setShowAddCaseModal(true)}
              className="text-xs font-semibold text-slate-700 hover:text-slate-900 border border-slate-200 rounded-full px-3 py-1 bg-white hover:bg-slate-50 transition-colors cursor-pointer"
            >
              + New Case
            </button>
          </div>

          <div className="space-y-2.5">
            {displayPriorityCases.map((c, i) => (
              <div
                key={i}
                onClick={() => navigate(`/victims/${c.id}`)}
                className="flex items-center gap-3 p-2.5 rounded-2xl hover:bg-slate-50 border border-transparent hover:border-slate-100 transition-all cursor-pointer group"
              >
                <div className={`w-8 h-8 rounded-xl ${c.iconBg} flex items-center justify-center flex-shrink-0 text-xs font-bold`}>
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-slate-800 truncate group-hover:text-[#0F4C3A]">
                    {c.id} · {c.title}
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
              onClick={() => setShowAddMemberModal(true)}
              className="text-xs font-semibold text-slate-700 hover:text-slate-900 border border-slate-200 rounded-full px-3 py-1 bg-white hover:bg-slate-50 transition-colors cursor-pointer flex items-center gap-1"
            >
              <UserPlus className="w-3 h-3" />
              <span>Add Member</span>
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

          <div className="flex flex-col items-center justify-center py-4 relative">
            <svg className="w-44 h-24 overflow-visible" viewBox="0 0 160 80">
              <path
                d="M 15 80 A 65 65 0 0 1 145 80"
                fill="none"
                stroke="#E2E8F0"
                strokeWidth="18"
                strokeLinecap="round"
              />
              <path
                d="M 15 80 A 65 65 0 0 1 115 25"
                fill="none"
                stroke="#0F4C3A"
                strokeWidth="18"
                strokeLinecap="round"
              />
            </svg>

            <div className="text-center mt-2">
              <span className="text-3xl font-extrabold text-slate-900 tracking-tight">68%</span>
              <p className="text-xs text-slate-400 font-medium">Cases Stabilized</p>
            </div>
          </div>

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
          <div className="absolute inset-0 opacity-15 pointer-events-none bg-[radial-gradient(#10B981_1px,transparent_1px)] [background-size:16px_16px]" />

          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-300 uppercase tracking-wider">Triage Live Monitor</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <p className="text-xs text-emerald-200/70 mt-1">Active case triage session</p>
          </div>

          <div className="my-6 text-center">
            <span className="text-3xl sm:text-4xl font-extrabold tracking-widest font-mono text-white">
              {formatTimer(timerSeconds)}
            </span>
          </div>

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
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Registered Victim Cases</h3>
            <p className="text-xs text-slate-400">Jurisdictionally anonymized longitudinal distress tracking</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
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

            <button
              onClick={load}
              className="w-9 h-9 rounded-full bg-slate-50 hover:bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 transition-colors cursor-pointer"
              title="Refresh Cases"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

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
                      {v.case_type?.replace('_', ' ').toUpperCase() || 'SC/ST PROTECTION'}
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
                      <TrendArrow trend={v.distress_trend || v.score_trend} />
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

      {/* ── MODAL 1: Add New Case Registration ── */}
      {showAddCaseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-slate-100">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-emerald-50 text-[#0F4C3A] flex items-center justify-center font-bold">
                  <Plus className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Register Victim Case</h3>
                  <p className="text-xs text-slate-400">Anonymized jurisdictional case entry</p>
                </div>
              </div>
              <button
                onClick={() => setShowAddCaseModal(false)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {caseSuccessMsg ? (
              <div className="my-8 text-center py-6">
                <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-3">
                  <Check className="w-6 h-6" />
                </div>
                <h4 className="text-base font-bold text-slate-900">{caseSuccessMsg}</h4>
                <p className="text-xs text-slate-400 mt-1">Updating registry dashboard...</p>
              </div>
            ) : (
              <form onSubmit={handleCreateCase} className="space-y-4 mt-5">
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Victim Anonymized ID</label>
                  <input
                    type="text"
                    value={newCaseId}
                    onChange={(e) => setNewCaseId(e.target.value)}
                    required
                    className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs px-4 py-2.5 rounded-xl font-mono font-bold"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Case Category / Type</label>
                  <select
                    value={newCaseType}
                    onChange={(e) => setNewCaseType(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs px-4 py-2.5 rounded-xl font-semibold"
                  >
                    <option value="intimidation">Witness Intimidation</option>
                    <option value="atrocity_act">SC/ST Atrocity Prevention Act</option>
                    <option value="sexual_violence">Sexual Violence & Trauma</option>
                    <option value="domestic_violence">Domestic Abuse / Violence</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1">District</label>
                    <input
                      type="text"
                      value={newCaseDistrict}
                      onChange={(e) => setNewCaseDistrict(e.target.value)}
                      required
                      className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs px-4 py-2.5 rounded-xl"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1">State</label>
                    <input
                      type="text"
                      value={newCaseState}
                      onChange={(e) => setNewCaseState(e.target.value)}
                      required
                      className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs px-4 py-2.5 rounded-xl"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={submittingCase}
                    className="w-full py-3 rounded-full bg-[#0F4C3A] hover:bg-[#0A392B] text-white text-xs font-bold shadow-sm transition-all"
                  >
                    {submittingCase ? 'Registering...' : 'Confirm Case Registration'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ── MODAL 2: Add Team Member ── */}
      {showAddMemberModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-slate-100">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-blue-50 text-blue-700 flex items-center justify-center font-bold">
                  <UserPlus className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Add Team Member</h3>
                  <p className="text-xs text-slate-400">Assign counsellor or officer</p>
                </div>
              </div>
              <button
                onClick={() => setShowAddMemberModal(false)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddMember} className="space-y-4 mt-5">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">Full Name & Title</label>
                <input
                  type="text"
                  placeholder="e.g. Dr. Sunil Mukherjee"
                  value={newMemberName}
                  onChange={(e) => setNewMemberName(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs px-4 py-2.5 rounded-xl"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">Role / Department</label>
                <select
                  value={newMemberRole}
                  onChange={(e) => setNewMemberRole(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs px-4 py-2.5 rounded-xl font-semibold"
                >
                  <option value="District Counsellor">District Clinical Counsellor</option>
                  <option value="Protection Officer">Witness Protection Officer</option>
                  <option value="Legal Aid Advocate">District Legal Services (DLSA)</option>
                  <option value="Psychiatrist">DMHP Consultant Psychiatrist</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">Assigned Case Task</label>
                <input
                  type="text"
                  placeholder="e.g. Follow-up trauma assessment"
                  value={newMemberTask}
                  onChange={(e) => setNewMemberTask(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs px-4 py-2.5 rounded-xl"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full py-3 rounded-full bg-[#0F4C3A] hover:bg-[#0A392B] text-white text-xs font-bold shadow-sm transition-all"
                >
                  Add Member to Team
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL 3: Secure Tele-Consultation Room ── */}
      {showTeleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-fade-in">
          <div className="bg-slate-900 rounded-3xl p-6 max-w-2xl w-full text-white shadow-2xl border border-slate-800">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <span className="w-3 h-3 rounded-full bg-emerald-500 animate-ping" />
                <div>
                  <h3 className="text-base font-bold text-white">Patna Case Multi-Disciplinary Tele-Consultation</h3>
                  <p className="text-xs text-slate-400">Encrypted Tele-MANAS Channel · Session #TL-9021</p>
                </div>
              </div>
              <button
                onClick={() => setShowTeleModal(false)}
                className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-400 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Video Feeds Simulation */}
            <div className="grid grid-cols-2 gap-4 my-6">
              <div className="aspect-video bg-slate-800 rounded-2xl flex flex-col items-center justify-center relative overflow-hidden border border-slate-700">
                <div className="w-16 h-16 rounded-full bg-emerald-900/60 border border-emerald-500/40 flex items-center justify-center text-emerald-400 text-xl font-bold">
                  PS
                </div>
                <p className="text-xs font-semibold text-slate-300 mt-2">Dr. Priya Sharma (DMHP)</p>
                <span className="absolute bottom-2 left-2 text-[10px] bg-black/60 px-2 py-0.5 rounded-md text-emerald-400 font-mono">
                  Audio Active
                </span>
              </div>

              <div className="aspect-video bg-slate-800 rounded-2xl flex flex-col items-center justify-center relative overflow-hidden border border-slate-700">
                <div className="w-16 h-16 rounded-full bg-blue-900/60 border border-blue-500/40 flex items-center justify-center text-blue-400 text-xl font-bold">
                  DO
                </div>
                <p className="text-xs font-semibold text-slate-300 mt-2">District Protection Officer</p>
                <span className="absolute bottom-2 left-2 text-[10px] bg-black/60 px-2 py-0.5 rounded-md text-slate-400 font-mono">
                  Connecting...
                </span>
              </div>
            </div>

            {/* In-Call Controls */}
            <div className="flex items-center justify-center gap-4 pt-2">
              <button
                onClick={() => setIsMuted(!isMuted)}
                className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                  isMuted ? 'bg-rose-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-white'
                }`}
                title={isMuted ? "Unmute" : "Mute"}
              >
                {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              <button
                onClick={() => setIsVideoOff(!isVideoOff)}
                className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                  isVideoOff ? 'bg-rose-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-white'
                }`}
                title={isVideoOff ? "Start Video" : "Stop Video"}
              >
                {isVideoOff ? <VideoOff className="w-5 h-5" /> : <Video className="w-5 h-5" />}
              </button>

              <button
                onClick={() => setShowTeleModal(false)}
                className="w-12 h-12 rounded-full bg-rose-600 hover:bg-rose-500 text-white flex items-center justify-center shadow-lg transition-transform active:scale-90"
                title="End Consultation"
              >
                <PhoneOff className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
