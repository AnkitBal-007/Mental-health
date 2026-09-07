import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, AlertCircle, Eye, EyeOff, Loader2 } from 'lucide-react';

const ROLE_CREDENTIALS = {
  district: { username: 'district_patna', label: 'District Officer', hint: 'District victim monitoring' },
  counsellor: { username: 'counsellor_anjali', label: 'Counsellor', hint: 'Assigned case management' },
  state: { username: 'state_bihar', label: 'State Cell', hint: 'State-level aggregated view' },
  national: { username: 'national_admin', label: 'National Admin', hint: 'Full national oversight' },
};

export default function Login() {
  const [username, setUsername] = useState('district_patna');
  const [password, setPassword] = useState('password123');
  const [showPassword, setShowPassword] = useState(false);
  const [selectedRole, setSelectedRole] = useState('district');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleRoleSelect = (role) => {
    setSelectedRole(role);
    setUsername(ROLE_CREDENTIALS[role].username);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Authentication failed. Check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F6F8] flex items-center justify-center px-4 py-12 font-sans">
      <div className="relative w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-200/90 flex items-center justify-center shadow-xs">
              <svg className="w-7 h-7 text-[#0F4C3A]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5" />
                <circle cx="12" cy="12" r="2.5" fill="currentColor" />
              </svg>
            </div>
            <div className="text-left">
              <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight leading-none">Saathi</h1>
              <p className="text-[11px] text-emerald-800 font-bold uppercase tracking-wider mt-0.5">Victim Distress Monitoring</p>
            </div>
          </div>
          <p className="text-slate-500 text-sm font-medium">Empathetic case management & early warning platform</p>
        </div>

        {/* Card */}
        <div className="bg-white border border-slate-100 rounded-3xl p-8 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900 mb-1 tracking-tight">Sign In</h2>
          <p className="text-slate-400 text-xs mb-6">Select a demo role for instant credentials</p>

          {/* Role Selector */}
          <div className="grid grid-cols-2 gap-2.5 mb-6">
            {Object.entries(ROLE_CREDENTIALS).map(([role, info]) => (
              <button
                key={role}
                type="button"
                onClick={() => handleRoleSelect(role)}
                className={`p-3 rounded-2xl border text-left transition-all ${
                  selectedRole === role
                    ? 'border-[#0F4C3A] bg-emerald-50/70 text-[#0F4C3A] shadow-xs'
                    : 'border-slate-200 bg-slate-50/60 text-slate-600 hover:border-slate-300 hover:bg-white'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <Shield className={`w-3.5 h-3.5 ${selectedRole === role ? 'text-[#0F4C3A]' : 'text-slate-400'}`} />
                  <span className="text-xs font-bold">{info.label}</span>
                </div>
                <p className="text-[11px] opacity-75 leading-tight">{info.hint}</p>
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wider">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                required
                className="w-full bg-[#F8FAFC] border border-slate-200 text-slate-900 placeholder-slate-400 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0F4C3A]/20 focus:border-[#0F4C3A] transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  required
                  className="w-full bg-[#F8FAFC] border border-slate-200 text-slate-900 placeholder-slate-400 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0F4C3A]/20 focus:border-[#0F4C3A] transition-all pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold rounded-2xl px-3.5 py-2.5">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#0F4C3A] hover:bg-[#0A392B] disabled:opacity-50 text-white font-bold rounded-full py-3 text-sm transition-all shadow-sm flex items-center justify-center gap-2 active:scale-98 cursor-pointer mt-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Authenticating…
                </>
              ) : (
                'Sign In to Saathi'
              )}
            </button>
          </form>

          <p className="text-center text-xs text-slate-400 font-medium mt-6">
            All sessions are encrypted · National Helpline 14566
          </p>
        </div>
      </div>
    </div>
  );
}
