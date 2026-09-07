/**
 * Simulation Page — Run scripted victim distress trajectories and watch the
 * ML pipeline + backend respond in real time.
 *
 * Scenarios:
 *   gradual_decline   — Scores start moderate and worsen over 8 turns
 *   sudden_trigger    — Stable, then sharp drop after a trigger event
 *   stable_low_risk   — Consistently low distress throughout
 *   recovery          — Starts high, gradually improves with support
 *
 * For each turn:
 *   1. Show the scripted "victim message"
 *   2. POST /analyze/text → get real sentiment + emotion from ML pipeline
 *   3. POST /check-ins → store in backend
 *   4. Chart updates live
 */

import React, { useState, useRef, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Area, AreaChart,
} from 'recharts';
import { Play, Square, ChevronRight, AlertTriangle, CheckCircle, Activity } from 'lucide-react';
import { Spinner } from '../components/ui';

import { BASE_URL } from '../api/client';

const ML_URL = import.meta.env.VITE_ML_URL || 'http://localhost:8001';
const API_URL = BASE_URL;

// ── Scenario scripts ────────────────────────────────────────────────────────
const SCENARIOS = {
  gradual_decline: {
    label: 'Gradual Decline',
    color: 'text-orange-400',
    borderColor: 'border-orange-500/30',
    bgColor: 'bg-orange-500/5',
    icon: '📉',
    description: 'Victim starts moderately okay, emotional state worsens across check-ins over several days.',
    turns: [
      { text: "I am managing somehow. Things are difficult but I am trying.", lang: 'en', delay: 1200 },
      { text: "Sleep is not good lately. I keep waking up at night worried.", lang: 'en', delay: 1200 },
      { text: "मुझे बहुत डर लग रहा है। रात को नींद नहीं आती।", lang: 'hi', delay: 1200 },
      { text: "I feel like no one understands what I am going through. I feel very alone.", lang: 'en', delay: 1200 },
      { text: "Everything feels hopeless. I do not know how long I can keep going like this.", lang: 'en', delay: 1200 },
      { text: "मुझे बहुत गुस्सा और दुख है। कोई मेरी बात नहीं सुनता।", lang: 'hi', delay: 1200 },
      { text: "I am scared all the time. I cannot even leave my house.", lang: 'en', delay: 1200 },
      { text: "I feel very low today. I don't want to talk to anyone.", lang: 'en', delay: 1200 },
    ],
  },
  sudden_trigger: {
    label: 'Sudden Trigger Event',
    color: 'text-red-400',
    borderColor: 'border-red-500/30',
    bgColor: 'bg-red-500/5',
    icon: '⚡',
    description: 'Victim is stable, then a threatening incident causes a sharp psychological drop.',
    turns: [
      { text: "Things have been okay this week. I am feeling a bit better.", lang: 'en', delay: 1200 },
      { text: "The court date went fine. I feel a little hopeful.", lang: 'en', delay: 1200 },
      { text: "I went to the market today. I feel safer now.", lang: 'en', delay: 1200 },
      { text: "Someone from the other side called me and threatened me today. I am very scared.", lang: 'en', delay: 1200 },
      { text: "मुझे धमकी मिली है। मैं बहुत डरी हुई हूँ, रो रही हूँ।", lang: 'hi', delay: 1200 },
      { text: "I cannot eat. I cannot sleep. I am terrified they will come for me.", lang: 'en', delay: 1200 },
      { text: "मुझे यहाँ से जाना है। मैं यहाँ सुरक्षित नहीं हूँ।", lang: 'hi', delay: 1200 },
      { text: "I am in severe distress. Please help me. I am very afraid.", lang: 'en', delay: 1200 },
    ],
  },
  stable_low_risk: {
    label: 'Stable / Low Risk',
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/30',
    bgColor: 'bg-emerald-500/5',
    icon: '✅',
    description: 'Victim is coping well with consistent support. Distress remains within acceptable range.',
    turns: [
      { text: "I am doing fine today. My family is supporting me.", lang: 'en', delay: 1200 },
      { text: "The counsellor session was very helpful. I feel understood.", lang: 'en', delay: 1200 },
      { text: "आज मैं ठीक हूँ। खाना खाया और थोड़ा आराम किया।", lang: 'hi', delay: 1200 },
      { text: "I went for a walk today. It helped clear my mind a little.", lang: 'en', delay: 1200 },
      { text: "Talking to my sister helped me a lot. I feel less alone.", lang: 'en', delay: 1200 },
      { text: "There are still difficult moments but overall I am managing.", lang: 'en', delay: 1200 },
    ],
  },
  recovery: {
    label: 'Recovery Trajectory',
    color: 'text-purple-400',
    borderColor: 'border-purple-500/30',
    bgColor: 'bg-purple-500/5',
    icon: '🌱',
    description: 'Victim starts in distress but progressively recovers with counselling and support interventions.',
    turns: [
      { text: "मैं बहुत परेशान हूँ। कुछ भी अच्छा नहीं लग रहा।", lang: 'hi', delay: 1200 },
      { text: "I feel hopeless. Nobody seems to care about my case.", lang: 'en', delay: 1200 },
      { text: "The counsellor visited today. It helped a little to talk.", lang: 'en', delay: 1200 },
      { text: "आज थोड़ा बेहतर लगा। काउंसलर से बात हुई।", lang: 'hi', delay: 1200 },
      { text: "My legal aid appointment is scheduled. I feel a bit more hopeful.", lang: 'en', delay: 1200 },
      { text: "I slept a little better last night. Things are slowly improving.", lang: 'en', delay: 1200 },
      { text: "मुझे लग रहा है कि मुझे मदद मिल रही है। थोड़ा ठीक लग रहा है।", lang: 'hi', delay: 1200 },
      { text: "I feel much better than I did a week ago. Thank you.", lang: 'en', delay: 1200 },
    ],
  },
};

// ── Tooltip ─────────────────────────────────────────────────────────────────
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 shadow-2xl text-xs">
      <p className="text-slate-400 mb-1">{label}</p>
      <p className="text-white font-bold text-base">{d?.score?.toFixed(1)}</p>
      {d?.emotion && <p className="text-indigo-400 capitalize mt-0.5">{d.emotion}</p>}
      {d?.sentiment && (
        <p className={`capitalize font-medium ${d.sentiment === 'negative' ? 'text-red-400' : d.sentiment === 'positive' ? 'text-emerald-400' : 'text-slate-400'}`}>
          {d.sentiment}
        </p>
      )}
    </div>
  );
}

// ── Turn message card ────────────────────────────────────────────────────────
function TurnCard({ turn, index, scenario }) {
  const s = SCENARIOS[scenario];
  const statusIcon = turn.status === 'analyzing' ? '⏳'
    : turn.status === 'done' ? '✓'
    : turn.status === 'error' ? '⚠'
    : '○';

  return (
    <div className={`border rounded-xl p-3 text-xs transition-all duration-300 ${
      turn.status === 'analyzing' ? `${s.borderColor} ${s.bgColor}` :
      turn.status === 'done' ? 'border-slate-700 bg-slate-800/40' :
      'border-slate-800 bg-slate-900'
    }`}>
      <div className="flex items-start gap-2">
        <span className="text-slate-500 font-mono w-4 flex-shrink-0">T{index + 1}</span>
        <div className="flex-1 min-w-0">
          <p className="text-slate-300 leading-relaxed">{turn.text}</p>
          {turn.lang === 'hi' && <span className="text-[10px] text-slate-600">Hindi</span>}
        </div>
        <span className={`flex-shrink-0 font-bold ${
          turn.status === 'done' ? 'text-emerald-400' :
          turn.status === 'analyzing' ? 'text-amber-400 animate-pulse' :
          turn.status === 'error' ? 'text-red-400' :
          'text-slate-700'
        }`}>{statusIcon}</span>
      </div>

      {turn.result && (
        <div className="mt-2 pt-2 border-t border-slate-700/50 flex flex-wrap gap-2">
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
            turn.result.sentiment === 'negative' ? 'bg-red-500/15 text-red-400 border-red-500/30' :
            turn.result.sentiment === 'positive' ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
            'bg-slate-700 text-slate-400 border-slate-600'
          }`}>{turn.result.sentiment}</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 capitalize">
            {turn.result.emotion}
          </span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-700 text-white border border-slate-600">
            Score: {turn.result.score?.toFixed(1)}
          </span>
          {turn.result.saved && <span className="text-[10px] text-emerald-600">✓ Saved to backend</span>}
        </div>
      )}
    </div>
  );
}

// ── Main Simulation ──────────────────────────────────────────────────────────
export default function Simulation() {
  const [scenario, setScenario] = useState('gradual_decline');
  const [victimId, setVictimId] = useState('VIC-2024-00483');
  const [running, setRunning] = useState(false);
  const [turns, setTurns] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [currentTurn, setCurrentTurn] = useState(-1);
  const [summary, setSummary] = useState(null);
  const abortRef = useRef(false);

  const s = SCENARIOS[scenario];

  const resetSim = () => {
    setTurns([]);
    setChartData([]);
    setCurrentTurn(-1);
    setSummary(null);
    setRunning(false);
    abortRef.current = false;
  };

  const handleScenarioChange = (key) => {
    setScenario(key);
    resetSim();
  };

  const runSimulation = useCallback(async () => {
    abortRef.current = false;
    setRunning(true);
    setSummary(null);

    const script = SCENARIOS[scenario].turns;
    const initialTurns = script.map((t) => ({ ...t, status: 'pending', result: null }));
    setTurns(initialTurns);
    setChartData([]);
    setCurrentTurn(0);

    const token = localStorage.getItem('token');
    const scores = [];

    for (let i = 0; i < script.length; i++) {
      if (abortRef.current) break;

      setCurrentTurn(i);
      setTurns((prev) =>
        prev.map((t, idx) => idx === i ? { ...t, status: 'analyzing' } : t)
      );

      await new Promise((r) => setTimeout(r, 600));

      let result = null;
      try {
        // 1. Analyze text
        const mlRes = await fetch(`${ML_URL}/analyze/text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: script[i].text, language: script[i].lang }),
        });

        const mlData = mlRes.ok ? await mlRes.json() : null;

        const sentLabel = mlData?.sentiment?.label || 'neutral';
        const emotionLabel = mlData?.emotions?.[0]?.label || 'neutral';
        const sentConf = mlData?.sentiment?.confidence || 0.5;
        const sentScore = sentLabel === 'positive' ? sentConf : sentLabel === 'negative' ? -sentConf : 0;

        // 2. Store check-in
        let saved = false;
        try {
          const ciRes = await fetch(`${API_URL}/check-ins`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
              victim_id: victimId,
              channel: 'simulation',
              text_content: script[i].text,
              sentiment_score: sentScore,
              emotion_label: emotionLabel,
              engagement_score: 0.75,
            }),
          });
          if (ciRes.ok) {
            const ciData = await ciRes.json();
            result = {
              sentiment: sentLabel,
              emotion: emotionLabel,
              score: ciData.distress_score ?? (50 + (sentScore * -25)),
              saved: true,
            };
            saved = true;
          }
        } catch {
          // Saved flag false, still show ML result
        }

        if (!result) {
          result = {
            sentiment: sentLabel,
            emotion: emotionLabel,
            score: 50 + (sentScore * -25) + (Math.random() * 10 - 5),
            saved: false,
          };
        }

        scores.push(result.score);

        setChartData((prev) => [
          ...prev,
          {
            label: `T${i + 1}`,
            score: result.score,
            sentiment: result.sentiment,
            emotion: result.emotion,
          },
        ]);

        setTurns((prev) =>
          prev.map((t, idx) => idx === i ? { ...t, status: 'done', result } : t)
        );
      } catch (err) {
        setTurns((prev) =>
          prev.map((t, idx) => idx === i ? { ...t, status: 'error', result: { error: err.message } } : t)
        );
      }

      await new Promise((r) => setTimeout(r, script[i].delay));
    }

    // Summary
    if (scores.length > 0) {
      const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
      const trend = scores[scores.length - 1] - scores[0];
      setSummary({
        avg: avg.toFixed(1),
        peak: Math.max(...scores).toFixed(1),
        trend: trend > 10 ? 'worsening' : trend < -10 ? 'improving' : 'stable',
        trendValue: trend.toFixed(1),
      });
    }

    setRunning(false);
  }, [scenario, victimId]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Distress Trajectory Simulation</h1>
        <p className="text-slate-400 text-sm mt-0.5">
          Run scripted check-in sequences through the live ML pipeline and observe real-time distress score evolution.
        </p>
      </div>

      {/* Config row */}
      <div className="card p-4 flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-48">
          <label className="block text-xs text-slate-500 mb-1.5 uppercase tracking-wider">Scenario</label>
          <select
            className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={scenario}
            onChange={(e) => handleScenarioChange(e.target.value)}
            disabled={running}
          >
            {Object.entries(SCENARIOS).map(([k, s]) => (
              <option key={k} value={k}>{s.icon} {s.label}</option>
            ))}
          </select>
        </div>
        <div className="w-52">
          <label className="block text-xs text-slate-500 mb-1.5 uppercase tracking-wider">Victim ID</label>
          <input
            className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={victimId}
            onChange={(e) => setVictimId(e.target.value)}
            disabled={running}
            placeholder="VIC-2024-XXXXX"
          />
        </div>
        <div className="flex gap-2.5">
          {!running ? (
            <button
              onClick={runSimulation}
              className="flex items-center gap-2 bg-[#0F4C3A] hover:bg-[#0A392B] text-white font-bold rounded-full px-6 py-2.5 text-xs transition-all shadow-sm active:scale-95 cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Run Simulation
            </button>
          ) : (
            <button
              onClick={() => { abortRef.current = true; setRunning(false); }}
              className="flex items-center gap-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold rounded-full px-6 py-2.5 text-xs transition-all cursor-pointer active:scale-95"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              Stop
            </button>
          )}
          {!running && turns.length > 0 && (
            <button onClick={resetSim} className="btn-ghost text-xs cursor-pointer">Reset</button>
          )}
        </div>
      </div>

      {/* Scenario info banner */}
      <div className={`p-5 rounded-3xl border bg-white shadow-sm flex items-start gap-3.5`}>
        <span className="text-3xl">{s.icon}</span>
        <div>
          <p className={`text-sm font-extrabold ${s.color}`}>{s.label}</p>
          <p className="text-slate-600 text-xs mt-0.5 font-medium">{s.description}</p>
          <p className="text-slate-400 text-[11px] mt-1 font-semibold">{s.turns.length} check-in turns · Real ML inference · Stored to live database</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Live Chart */}
        <div className="lg:col-span-3 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#0F4C3A]" />
              Live Distress Score Trajectory
            </h2>
            {running && (
              <span className="flex items-center gap-1.5 text-xs font-bold text-amber-600 animate-pulse bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
                <div className="w-1.5 h-1.5 bg-amber-500 rounded-full" />
                Simulating turn {currentTurn + 1}…
              </span>
            )}
          </div>

          {chartData.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-slate-400 gap-3">
              <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center text-slate-400">
                <Play className="w-5 h-5 ml-0.5" />
              </div>
              <p className="text-xs font-semibold">Click "Run Simulation" to start the trajectory</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Alert', position: 'right', fontSize: 10, fill: '#ef4444' }} />
                <ReferenceLine y={50} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'Watch', position: 'right', fontSize: 10, fill: '#f59e0b' }} />
                <Area type="monotone" dataKey="score" stroke="#0F4C3A" strokeWidth={2.5} fill="#0F4C3A" fillOpacity={0.08}
                  dot={{ r: 4, fill: '#0F4C3A', strokeWidth: 0 }}
                  activeDot={{ r: 6, fill: '#10B981', stroke: '#fff', strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}

          {/* Summary */}
          {summary && (
            <div className={`mt-4 grid grid-cols-3 gap-3 pt-4 border-t border-slate-100`}>
              {[
                { label: 'Avg Score', value: summary.avg },
                { label: 'Peak Score', value: summary.peak },
                { label: 'Trend', value: <span className={summary.trend === 'worsening' ? 'text-rose-600 font-bold' : summary.trend === 'improving' ? 'text-emerald-700 font-bold' : 'text-slate-600 font-bold'}>
                  {summary.trend === 'worsening' ? '↑' : summary.trend === 'improving' ? '↓' : '→'} {summary.trend} ({summary.trendValue > 0 ? '+' : ''}{summary.trendValue})
                </span> },
              ].map(({ label, value }) => (
                <div key={label} className="text-center p-3 rounded-2xl bg-slate-50 border border-slate-100">
                  <p className="text-[10px] font-bold text-slate-400 mb-0.5 uppercase tracking-wider">{label}</p>
                  <p className="text-lg font-extrabold text-slate-900">{value}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Turn log */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col">
          <h2 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2 flex-shrink-0">
            <ChevronRight className="w-4 h-4 text-slate-400" />
            Turn-by-Turn Feed
          </h2>
          <div className="space-y-2.5 overflow-y-auto flex-1 max-h-80 pr-1">
            {turns.length === 0 ? (
              <p className="text-slate-400 text-xs text-center py-12 font-medium">Turn results will stream here live</p>
            ) : (
              turns.map((turn, i) => (
                <TurnCard key={i} turn={turn} index={i} scenario={scenario} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
