import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, Bell, LogOut, Users, Settings, HelpCircle,
  Search, Mail, ArrowUpRight, MessageCircle, FlaskConical,
  BarChart3, CheckSquare, Shield, PhoneCall
} from 'lucide-react';

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const roleDisplay = {
    district: `${user?.district || 'Patna'} District Cell`,
    state: `${user?.state || 'Bihar'} State Cell`,
    national: 'National Protection Cell',
    counsellor: 'Senior Trauma Counsellor',
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#F4F6F8] font-sans">
      {/* ── Left Sidebar ── */}
      <aside className="w-64 flex-shrink-0 bg-white border-r border-slate-100 flex flex-col justify-between py-6 px-4 z-20">
        <div>
          {/* Brand Logo */}
          <div className="flex items-center gap-3 px-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200/80 flex items-center justify-center shadow-xs">
              {/* Stylized Double Loop / Care Emblem */}
              <svg className="w-6 h-6 text-[#0F4C3A]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5" />
                <circle cx="12" cy="12" r="2.5" fill="currentColor" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight leading-none">Sahayak</h1>
              <p className="text-[10px] text-emerald-700 font-semibold tracking-wider uppercase mt-0.5">Victim Care & Alert</p>
            </div>
          </div>

          {/* MENU Section */}
          <div className="space-y-6">
            <div>
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">MENU</p>
              <nav className="space-y-1">
                <NavLink
                  to="/dashboard"
                  className={({ isActive }) =>
                    `relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                      isActive
                        ? 'text-slate-900 bg-slate-50'
                        : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50/70'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-[#0F4C3A] rounded-r-full" />
                      )}
                      <LayoutDashboard className={`w-4 h-4 ${isActive ? 'text-[#0F4C3A]' : 'text-slate-400'}`} />
                      <span>Dashboard</span>
                    </>
                  )}
                </NavLink>

                <NavLink
                  to="/alerts"
                  className={({ isActive }) =>
                    `relative flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                      isActive
                        ? 'text-slate-900 bg-slate-50'
                        : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50/70'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <div className="flex items-center gap-3">
                        {isActive && (
                          <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-[#0F4C3A] rounded-r-full" />
                        )}
                        <Bell className={`w-4 h-4 ${isActive ? 'text-[#0F4C3A]' : 'text-slate-400'}`} />
                        <span>Alerts Feed</span>
                      </div>
                      <span className="bg-[#0F4C3A] text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                        Live
                      </span>
                    </>
                  )}
                </NavLink>

                <NavLink
                  to="/simulation"
                  className={({ isActive }) =>
                    `relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                      isActive
                        ? 'text-slate-900 bg-slate-50'
                        : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50/70'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-[#0F4C3A] rounded-r-full" />
                      )}
                      <FlaskConical className={`w-4 h-4 ${isActive ? 'text-[#0F4C3A]' : 'text-slate-400'}`} />
                      <span>Simulation Lab</span>
                    </>
                  )}
                </NavLink>

                <a
                  href="/chatbot"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-semibold text-slate-500 hover:text-slate-900 hover:bg-slate-50/70 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <MessageCircle className="w-4 h-4 text-emerald-600" />
                    <span>Saheli Didi AI</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400" />
                </a>
              </nav>
            </div>

            {/* GENERAL Section */}
            <div>
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">GENERAL</p>
              <nav className="space-y-1">
                <button
                  type="button"
                  onClick={() => alert("Settings configuration is managed via Environment Variables & Admin Tokens.")}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-slate-500 hover:text-slate-900 hover:bg-slate-50/70 transition-all text-left"
                >
                  <Settings className="w-4 h-4 text-slate-400" />
                  <span>Settings</span>
                </button>

                <button
                  type="button"
                  onClick={() => alert("National Atrocity Helpline: 14566\nEmergency SOS: 112\nSahayak Case Monitoring System Version 2.0")}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-slate-500 hover:text-slate-900 hover:bg-slate-50/70 transition-all text-left"
                >
                  <HelpCircle className="w-4 h-4 text-slate-400" />
                  <span>Help & Helpline</span>
                </button>

                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-rose-600 hover:bg-rose-50/80 transition-all text-left"
                >
                  <LogOut className="w-4 h-4 text-rose-500" />
                  <span>Logout</span>
                </button>
              </nav>
            </div>
          </div>
        </div>

        {/* Bottom App Promo Card (Matching Donezo Emerald Wave Card) */}
        <div className="mt-4 p-4 rounded-2xl bg-[#093528] text-white relative overflow-hidden shadow-md">
          {/* Subtle wavy decorative rings */}
          <div className="absolute -right-6 -bottom-6 w-28 h-28 rounded-full border-4 border-emerald-500/20 pointer-events-none" />
          <div className="absolute -right-10 -bottom-10 w-36 h-36 rounded-full border border-emerald-400/10 pointer-events-none" />

          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded-md bg-emerald-500/20 flex items-center justify-center">
              <PhoneCall className="w-3.5 h-3.5 text-emerald-300" />
            </div>
            <span className="text-[11px] font-bold text-emerald-300 tracking-wider uppercase">SOS Helpline</span>
          </div>

          <p className="text-sm font-bold text-white mb-0.5">National Care App</p>
          <p className="text-[11px] text-emerald-200/80 mb-3">Toll-free 14566 · 24/7 AI distress triage</p>

          <a
            href="/chatbot"
            target="_blank"
            rel="noopener noreferrer"
            className="block text-center w-full py-2 bg-[#175A44] hover:bg-[#1C6C52] text-white font-semibold text-xs rounded-xl shadow-xs transition-all active:scale-95"
          >
            Launch Saheli Didi
          </a>
        </div>
      </aside>

      {/* ── Main Content Area with Sticky Header ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header Navigation Bar */}
        <header className="h-20 bg-white/90 backdrop-blur-md border-b border-slate-100 flex items-center justify-between px-8 flex-shrink-0 z-10">
          {/* Search Input Bar with Shortcut Indicator */}
          <div className="relative w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search victim ID, alert, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#F4F6F8] text-slate-800 placeholder-slate-400 text-sm pl-11 pr-14 py-2.5 rounded-full border border-transparent focus:border-slate-200 focus:bg-white focus:outline-none transition-all"
            />
            <kbd className="absolute right-3.5 top-1/2 -translate-y-1/2 bg-white border border-slate-200 text-slate-400 text-[10px] font-medium px-2 py-0.5 rounded-md shadow-2xs">
              ⌘F
            </kbd>
          </div>

          {/* Right Header Controls & Profile Pill */}
          <div className="flex items-center gap-4">
            {/* Notification Bell */}
            <NavLink
              to="/alerts"
              className="relative w-10 h-10 rounded-full bg-[#F4F6F8] hover:bg-slate-100 flex items-center justify-center text-slate-600 transition-colors"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-emerald-500 rounded-full ring-2 ring-white" />
            </NavLink>

            {/* Direct Chat / Message */}
            <a
              href="/chatbot"
              target="_blank"
              rel="noopener noreferrer"
              className="w-10 h-10 rounded-full bg-[#F4F6F8] hover:bg-slate-100 flex items-center justify-center text-slate-600 transition-colors"
            >
              <Mail className="w-4 h-4" />
            </a>

            {/* User Profile Card Pill */}
            <div className="flex items-center gap-3 pl-3 border-l border-slate-100">
              {/* Profile Avatar */}
              <div className="w-10 h-10 rounded-full bg-emerald-100 border border-emerald-300 flex items-center justify-center overflow-hidden shadow-xs">
                <span className="text-sm font-bold text-emerald-800">
                  {user?.username ? user.username.slice(0, 2).toUpperCase() : 'SK'}
                </span>
              </div>
              <div className="text-left hidden sm:block">
                <p className="text-sm font-bold text-slate-900 leading-tight">
                  {user?.full_name || user?.username || 'District Officer'}
                </p>
                <p className="text-xs text-slate-400 font-medium">
                  {user?.email || roleDisplay[user?.role] || 'officer@sih.gov.in'}
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto bg-[#F4F6F8] p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
