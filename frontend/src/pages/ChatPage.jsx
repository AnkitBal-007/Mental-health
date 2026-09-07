/**
 * Standalone Chatbot page — Full-Screen / Multi-Device Caring Support Interface.
 * Accessible at /chatbot (Direct access for victims / complainants).
 * Optimized for Mobile (iOS/Android), Tablet, and Desktop PC.
 */

import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import ChatWidget from '../chatbot/ChatWidget';
import { Shield, PhoneCall, Heart, ArrowLeft, Lock, Sparkles } from 'lucide-react';

export default function ChatPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const victimId = searchParams.get('vic') || null;
  const [done, setDone] = useState(false);

  return (
    <div className="min-h-dvh sm:min-h-screen bg-[#F4F6F8] flex flex-col font-sans">
      {/* ── Top Header Bar (Desktop & Tablet) ── */}
      <header className="hidden sm:flex h-16 bg-white border-b border-slate-100 items-center justify-between px-6 lg:px-12 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl overflow-hidden border border-emerald-200/80 shadow-2xs bg-white flex-shrink-0">
            <img src="/logo.png" alt="Saathi Logo" className="w-full h-full object-cover" />
          </div>
          <div>
            <h1 className="text-lg font-extrabold text-slate-900 tracking-tight leading-tight">Saathi</h1>
            <p className="text-[10px] text-emerald-800 font-bold uppercase tracking-wider">Your Mind Matters</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-semibold text-slate-500">
          <span className="hidden md:flex items-center gap-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1 rounded-full">
            <Lock className="w-3.5 h-3.5 text-emerald-700" />
            End-to-End Encrypted & Private
          </span>
          <a
            href="tel:14566"
            className="flex items-center gap-1.5 text-slate-700 hover:text-slate-900 bg-white border border-slate-200 px-3 py-1 rounded-full shadow-2xs transition-colors"
          >
            <PhoneCall className="w-3.5 h-3.5 text-emerald-700" />
            <span>Toll-Free 14566</span>
          </a>
        </div>
      </header>

      {/* ── Main Responsive Layout Container ── */}
      <div className="flex-1 flex items-center justify-center p-0 sm:p-6 lg:p-8">
        <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Desktop Left Info Column (Hidden on Mobile/Tablet) */}
          <div className="hidden lg:flex lg:col-span-4 flex-col gap-5 pr-4">
            <div>
              <span className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold px-3 py-1 rounded-full mb-3">
                <Heart className="w-3.5 h-3.5 text-emerald-700 fill-current" />
                Elder Sister Support
              </span>
              <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight leading-snug">
                You don't have to face anything alone.
              </h2>
              <p className="text-slate-500 text-xs leading-relaxed mt-2 font-medium">
                Saheli Didi is here to listen to your feelings without judgement. Everything you say is secure, encrypted, and reviewed only by licensed care personnel.
              </p>
            </div>

            {/* Helpline Card */}
            <div className="p-5 rounded-3xl bg-[#093528] text-white shadow-sm relative overflow-hidden">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-6 h-6 rounded-md bg-emerald-500/20 flex items-center justify-center">
                  <PhoneCall className="w-3.5 h-3.5 text-emerald-300" />
                </div>
                <span className="text-[11px] font-bold text-emerald-300 uppercase tracking-wider">Emergency SOS</span>
              </div>
              <p className="text-sm font-bold text-white mb-1">24/7 Crisis Assistance</p>
              <div className="space-y-1 text-xs text-emerald-200/80 font-medium mt-3">
                <p>• Police & Immediate Help: <strong className="text-white">112</strong></p>
                <p>• Women Helpline: <strong className="text-white">181</strong></p>
                <p>• Tele-MANAS Mental Health: <strong className="text-white">14416</strong></p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-[11px] text-slate-400 font-medium">
              <Shield className="w-4 h-4 text-emerald-700" />
              <span>National Atrocity Helpline (NHAA 14566)</span>
            </div>
          </div>

          {/* Main Chat Box Container (Full Screen on Mobile, Centered on PC/Tablet) */}
          <div className="lg:col-span-8 w-full">
            {done ? (
              <div className="text-center space-y-4 py-16 p-8 rounded-3xl bg-white border border-slate-100 shadow-md">
                <div className="w-20 h-20 rounded-3xl overflow-hidden border-2 border-emerald-200 shadow-md mx-auto">
                  <img src="/saheli_avatar.jpg" alt="Saheli Didi" className="w-full h-full object-cover" />
                </div>
                <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                  Thank you for talking, take care
                </h2>
                <p className="text-slate-500 text-xs sm:text-sm font-medium max-w-md mx-auto leading-relaxed">
                  Your check-in has been logged safely. Your designated protection cell and counsellors have been updated.
                </p>
                <p className="text-emerald-800 text-xs font-bold">
                  दीदी हमेशा आपके साथ हैं। जब भी जरूरत हो, आप वापस आ सकती हैं।
                </p>
                <div className="pt-2">
                  <button
                    onClick={() => setDone(false)}
                    className="px-6 py-3 rounded-full bg-[#0F4C3A] hover:bg-[#0A392B] text-white text-xs sm:text-sm font-bold transition shadow-sm active:scale-95 cursor-pointer"
                  >
                    Start a New Conversation
                  </button>
                </div>
              </div>
            ) : (
              <ChatWidget
                victimId={victimId}
                onClose={() => setDone(true)}
                embedded={false}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
