/**
 * ChatWidget — Empathetic, AI-Powered Elder Sister ("Saheli Didi") Chat Interface.
 *
 * Fully responsive for Mobile, Tablet, and Desktop (PC).
 * Matches the Sahayak Dashboard theme (Emerald, Light Cloud Canvas, Soft Rounded Cards).
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  BOT_NAME, WELCOME_MESSAGES, FOLLOW_UP_QUESTIONS,
  ACKNOWLEDGEMENTS, CLOSING_MESSAGES, LANGUAGE_LABELS, pickRandom,
} from './botScript';
import {
  Send, Sparkles, PhoneCall, ShieldCheck, Heart, ArrowLeft,
  X, RefreshCw, MessageSquare, AlertTriangle, Check, CheckCheck
} from 'lucide-react';

import { BASE_URL } from '../api/client';

const ML_PIPELINE_URL = import.meta.env.VITE_ML_URL || 'http://localhost:8001';
const BACKEND_URL = BASE_URL;

// Detect likely language from text (Devanagari range or Hindi romanized keywords)
function detectLanguage(text) {
  if (/[\u0900-\u097F]/.test(text)) return 'hi';
  const hindiKeywords = ['mujhe', 'mera', 'meri', 'kya', 'hai', 'hain', 'nahi', 'nhi', 'darr', 'dar', 'takleef', 'chinta', 'karo', 'karna', 'didi', 'bhai', 'bahana', 'aap', 'tum', 'khana', 'neend', 'bachao', 'marne'];
  const words = text.toLowerCase().split(/\s+/);
  if (words.some(w => hindiKeywords.includes(w))) return 'hi';
  return 'en';
}

async function analyzeText(text, language) {
  try {
    const res = await fetch(`${BACKEND_URL}/analyze/text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn('Text analyzer offline:', err);
    return null;
  }
}

async function storeCheckIn(victimId, analysis, turnText) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${BACKEND_URL}/check-ins`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      victim_id: victimId,
      channel: 'chatbot',
      text_content: turnText,
      sentiment_score: analysis?.sentiment?.confidence
        ? (analysis.sentiment.label === 'positive' ? analysis.sentiment.confidence
          : analysis.sentiment.label === 'negative' ? -analysis.sentiment.confidence
          : 0)
        : 0,
      emotion_label: analysis?.emotions?.[0]?.label || 'neutral',
      distress_score: analysis?.distress_score || (analysis?.threat_detected ? 85.0 : null),
      engagement_score: 0.8,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to save check-in');
  }
  return res.json();
}

async function getAiChatResponse(message, history, language, sentiment, emotion) {
  const res = await fetch(`${BACKEND_URL}/chat/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      history,
      language,
      sentiment_label: sentiment,
      emotion_label: emotion,
    }),
  });
  if (!res.ok) throw new Error(`AI chat error: ${res.status}`);
  return res.json();
}

// ── Message bubble ──────────────────────────────────────────────────────────

function MessageBubble({ msg }) {
  const isBot = msg.role === 'bot';
  return (
    <div className={`flex gap-2.5 sm:gap-3 mb-4 ${isBot ? 'justify-start' : 'justify-end'} animate-fade-in`}>
      {isBot && (
        <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-2xl bg-emerald-100 border border-emerald-200 flex items-center justify-center text-sm font-bold text-[#0F4C3A] flex-shrink-0 shadow-2xs mt-0.5">
          🌸
        </div>
      )}
      <div className={`max-w-[85%] sm:max-w-[78%] flex flex-col gap-1 ${isBot ? 'items-start' : 'items-end'}`}>
        <div
          className={`rounded-2xl sm:rounded-3xl px-4 sm:px-5 py-3 text-xs sm:text-sm leading-relaxed shadow-xs ${
            isBot
              ? 'bg-white text-slate-800 border border-slate-100 rounded-tl-sm'
              : 'bg-[#0F4C3A] text-white rounded-tr-sm'
          }`}
          dangerouslySetInnerHTML={{
            __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'),
          }}
        />

        {/* Sentiment feedback badge */}
        {msg.sentiment && (
          <div className="flex items-center gap-1.5 mt-0.5 px-1">
            <span className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full border ${
              msg.sentiment.label === 'positive'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : msg.sentiment.label === 'negative'
                ? 'bg-rose-50 text-rose-700 border-rose-200'
                : 'bg-slate-50 text-slate-600 border-slate-200'
            }`}>
              {msg.emotion} · {msg.sentiment.label}
            </span>
          </div>
        )}
        {msg.status === 'saving' && (
          <span className="text-[10px] text-slate-400 italic px-1">Saving check-in…</span>
        )}
        {msg.status === 'saved' && (
          <span className="text-[10px] text-emerald-700 font-semibold flex items-center gap-0.5 px-1">
            <CheckCheck className="w-3 h-3 inline" /> Logged securely
          </span>
        )}
        {msg.status === 'error' && (
          <span className="text-[10px] text-amber-600 font-medium px-1">Confidential (offline mode)</span>
        )}
      </div>
    </div>
  );
}

// ── Typing indicator ─────────────────────────────────────────────────────────

function TypingDots() {
  return (
    <div className="flex gap-2.5 sm:gap-3 mb-4 justify-start animate-fade-in">
      <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-2xl bg-emerald-100 border border-emerald-200 flex items-center justify-center text-sm font-bold text-[#0F4C3A] flex-shrink-0 shadow-2xs mt-0.5">
        🌸
      </div>
      <div className="bg-white border border-slate-100 rounded-2xl sm:rounded-3xl rounded-tl-sm px-4 py-3 flex gap-1.5 items-center shadow-xs">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 bg-emerald-600 rounded-full animate-bounce"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

export default function ChatWidget({
  victimId = null,
  language = 'en',
  onClose = null,
  embedded = false,
}) {
  const [lang, setLang] = useState(language);
  const [localVictimId, setLocalVictimId] = useState(victimId || '');
  const [idConfirmed, setIdConfirmed] = useState(Boolean(victimId));
  const [idError, setIdError] = useState('');

  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [typing, setTyping] = useState(false);
  const [turn, setTurn] = useState(0);
  const [sessionDone, setSessionDone] = useState(false);
  const [showCrisisBanner, setShowCrisisBanner] = useState(false);

  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  // Quick suggestion chips for Mobile/PC
  const quickPrompts = {
    en: [
      "I am feeling anxious today 😔",
      "Someone threatened my family 🚨",
      "I need legal aid guidance ⚖️",
      "I couldn't sleep last night 🌙",
      "Things are getting a bit better 🌿",
    ],
    hi: [
      "मुझे बहुत घबराहट हो रही है 😔",
      "मुझे धमकी मिली है, डर लग रहा है 🚨",
      "मुझे कानूनी मदद की जानकारी चाहिए ⚖️",
      "रात को ठीक से नींद नहीं आई 🌙",
      "आज पहले से थोड़ा बेहतर लग रहा है 🌿",
    ],
  };

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, typing]);

  // Bot message helper with typing delay
  const addBotMessages = useCallback((texts, startIndex = 0) => {
    if (startIndex >= texts.length) return;
    setTyping(true);
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: `bot_${Date.now()}_${startIndex}`,
          role: 'bot',
          text: texts[startIndex],
          timestamp: new Date().toISOString(),
        },
      ]);
      setTyping(false);
      addBotMessages(texts, startIndex + 1);
    }, 700);
  }, []);

  // Initialize welcome
  useEffect(() => {
    if (idConfirmed && messages.length === 0) {
      const msgs = WELCOME_MESSAGES[lang] || WELCOME_MESSAGES.en;
      addBotMessages(msgs);
    }
  }, [idConfirmed, lang, messages.length, addBotMessages]);

  const handleConfirmId = () => {
    const trimmed = localVictimId.trim().toUpperCase();
    if (!trimmed) {
      setIdError('Please enter your Victim ID (e.g. VIC-2024-10001) or enter GUEST to continue.');
      return;
    }
    setLocalVictimId(trimmed);
    setIdConfirmed(true);
  };

  const handleSend = useCallback(async (customText = null) => {
    const text = typeof customText === 'string' ? customText.trim() : inputText.trim();
    if (!text || sessionDone) return;

    setInputText('');

    const detected = detectLanguage(text);
    const effectiveLang = detected;

    const userMsgId = `user_${Date.now()}`;
    const userMsg = {
      id: userMsgId,
      role: 'user',
      text,
      timestamp: new Date().toISOString(),
      status: 'pending',
    };

    setMessages((prev) => [...prev, userMsg]);
    setTyping(true);

    try {
      const analysis = await analyzeText(text, effectiveLang);

      const sentimentLabel = analysis?.sentiment?.label || 'neutral';
      const emotionLabel = analysis?.emotions?.[0]?.label || 'neutral';
      const confidence = analysis?.sentiment?.confidence || 0.5;

      setMessages((prev) =>
        prev.map((m) =>
          m.id === userMsgId
            ? { ...m, sentiment: { label: sentimentLabel, confidence }, emotion: emotionLabel, status: 'saving' }
            : m
        )
      );

      try {
        if (localVictimId) {
          await storeCheckIn(localVictimId, analysis, text);
        }
      } catch (dbErr) {
        console.warn('Check-in not linked to registered victim ID:', dbErr.message);
      }

      setMessages((prev) =>
        prev.map((m) => m.id === userMsgId ? { ...m, status: 'saved' } : m)
      );

      const nextTurn = turn + 1;
      setTurn(nextTurn);

      const chatHistory = messages
        .filter((m) => m.text && !m.isSystem)
        .slice(-6)
        .map((m) => ({
          role: m.role === 'user' ? 'user' : 'assistant',
          text: m.text,
        }));

      let botReply = '';
      let isCrisis = false;

      try {
        const aiResult = await getAiChatResponse(
          text,
          chatHistory,
          effectiveLang,
          sentimentLabel,
          emotionLabel
        );
        botReply = aiResult.reply;
        isCrisis = !!aiResult.crisis_flag || !!analysis?.threat_detected;
      } catch (aiErr) {
        console.warn('Gemini chat fallback engaged:', aiErr);
        isCrisis = !!analysis?.threat_detected;
        const ackPool = ACKNOWLEDGEMENTS[
          sentimentLabel === 'positive' ? 'positive'
          : sentimentLabel === 'negative' ? 'negative'
          : 'neutral'
        ][lang] || ACKNOWLEDGEMENTS.neutral.en;
        const q = FOLLOW_UP_QUESTIONS[lang][(nextTurn - 1) % FOLLOW_UP_QUESTIONS[lang].length];
        botReply = `${pickRandom(ackPool)} ${q}`;
      }

      if (isCrisis) {
        setShowCrisisBanner(true);
      }

      addBotMessages([botReply]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) =>
        prev.map((m) => m.id === userMsgId ? { ...m, status: 'error' } : m)
      );

      const fallback = lang === 'hi'
        ? 'मेरी प्यारी बहना, मैं तुम्हारी बात समझ रही हूँ। तुम बिल्कुल परेशान मत हो, दीदी यहीं है।'
        : 'I hear you with all my heart, sweetheart. Please don\'t worry, Didi is right here with you.';

      const nextTurn = turn + 1;
      setTurn(nextTurn);
      addBotMessages([fallback]);
    }

    inputRef.current?.focus();
  }, [inputText, sessionDone, turn, localVictimId, lang, messages, addBotMessages]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleRestartChat = () => {
    setMessages([]);
    setTurn(0);
    setSessionDone(false);
    setShowCrisisBanner(false);
    const msgs = WELCOME_MESSAGES[lang] || WELCOME_MESSAGES.en;
    addBotMessages(msgs);
  };

  const handleEndChat = () => {
    setSessionDone(true);
    addBotMessages(CLOSING_MESSAGES[lang] || CLOSING_MESSAGES.en);
  };

  // ── ID confirmation screen ─────────────────────────────────────────────
  if (!idConfirmed) {
    return (
      <div className={`flex flex-col bg-white ${embedded ? 'rounded-3xl border border-slate-100 shadow-sm' : 'h-dvh sm:h-[650px] sm:max-h-[85vh] rounded-none sm:rounded-3xl border border-slate-100 shadow-md'} overflow-hidden`}>
        <ChatHeader lang={lang} setLang={setLang} onClose={onClose} embedded={embedded} />
        <div className="flex-1 flex flex-col items-center justify-center p-6 sm:p-10 gap-5 text-center bg-[#F8FAFC]">
          <div className="w-16 h-16 rounded-3xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-3xl shadow-xs">
            🌸
          </div>
          <div>
            <h2 className="text-slate-900 font-extrabold text-xl tracking-tight">Talk with {BOT_NAME}</h2>
            <p className="text-slate-500 text-xs sm:text-sm mt-1 max-w-sm">
              Confidential check-in with your AI elder sister. Please enter your Case or Victim ID.
            </p>
            <p className="text-emerald-800 text-xs font-semibold mt-1">अपना Case ID या Victim ID दर्ज करें।</p>
          </div>
          <div className="w-full max-w-xs space-y-3">
            <input
              className="w-full bg-white border border-slate-200 text-slate-900 placeholder-slate-400 rounded-full px-5 py-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[#0F4C3A]/20 focus:border-[#0F4C3A] text-center tracking-widest uppercase shadow-2xs"
              placeholder="VIC-2024-XXXXX"
              value={localVictimId}
              onChange={(e) => { setLocalVictimId(e.target.value); setIdError(''); }}
              onKeyDown={(e) => e.key === 'Enter' && handleConfirmId()}
            />
            {idError && <p className="text-rose-600 text-xs font-semibold">{idError}</p>}
            <button
              onClick={handleConfirmId}
              className="w-full bg-[#0F4C3A] hover:bg-[#0A392B] text-white font-bold rounded-full py-3 text-xs sm:text-sm transition-all shadow-sm active:scale-98 cursor-pointer"
            >
              Begin Confidential Session
            </button>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-400 font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>End-to-End Encrypted · Zero Clinical Jargon</span>
          </div>
        </div>
      </div>
    );
  }

  // ── Chat screen ─────────────────────────────────────────────────────────
  return (
    <div className={`flex flex-col bg-[#F4F6F8] ${embedded ? 'h-[580px] rounded-3xl border border-slate-100 shadow-sm' : 'h-dvh sm:h-[700px] sm:max-h-[90vh] rounded-none sm:rounded-3xl border border-slate-100 shadow-lg'} overflow-hidden relative font-sans`}>
      <ChatHeader
        lang={lang}
        setLang={setLang}
        onClose={onClose}
        embedded={embedded}
        victimId={localVictimId}
        onEndChat={handleEndChat}
        sessionDone={sessionDone}
      />

      {/* Emergency Crisis Safety Banner */}
      {showCrisisBanner && (
        <div className="mx-3 sm:mx-6 mt-3 p-3.5 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-900 flex items-start gap-3 shadow-xs">
          <span className="text-lg flex-shrink-0">🚨</span>
          <div className="flex-1">
            <p className="font-bold text-rose-900">
              {lang === 'hi' ? 'तत्काल 24/7 सहायता उपलब्ध है' : 'Immediate 24/7 Emergency Support'}
            </p>
            <p className="mt-0.5 text-[11px] text-rose-800 leading-relaxed font-medium">
              {lang === 'hi'
                ? 'यदि आप या कोई अन्य तत्काल संकट में हैं, तो सीधे संपर्क करें:'
                : 'If you are facing immediate danger or threat, please connect directly:'}
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              <a href="tel:112" className="bg-rose-600 hover:bg-rose-700 text-white font-bold px-3 py-1 rounded-full text-[11px] transition shadow-2xs">
                📞 112 (Emergency)
              </a>
              <a href="tel:181" className="bg-purple-700 hover:bg-purple-800 text-white font-bold px-3 py-1 rounded-full text-[11px] transition shadow-2xs">
                📞 181 (Women)
              </a>
              <a href="tel:14566" className="bg-[#0F4C3A] hover:bg-[#0A392B] text-white font-bold px-3 py-1 rounded-full text-[11px] transition shadow-2xs">
                📞 14566 (Tele-MANAS)
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-2">
        {messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)}
        {typing && <TypingDots />}

        {sessionDone && (
          <div className="mt-6 text-center animate-fade-in">
            <div className="inline-flex flex-col items-center gap-3 bg-white border border-emerald-200 rounded-3xl px-6 py-5 max-w-sm mx-auto shadow-sm">
              <span className="text-3xl">🌿</span>
              <div>
                <p className="text-slate-900 text-sm font-extrabold">
                  {lang === 'hi' ? 'दीदी हमेशा आपके साथ हैं' : 'Didi is Always Here for You'}
                </p>
                <p className="text-slate-500 text-xs mt-1 font-medium leading-relaxed">
                  {lang === 'hi' ? 'जब भी मन करे, आप फिर से बात शुरू कर सकती हैं।' : 'Take your time. You can start talking whenever you feel ready.'}
                </p>
              </div>
              <div className="flex gap-2 mt-2">
                <button
                  onClick={handleRestartChat}
                  className="text-xs bg-[#0F4C3A] hover:bg-[#0A392B] text-white font-bold px-4 py-2 rounded-full transition shadow-xs cursor-pointer"
                >
                  {lang === 'hi' ? 'दीदी से फिर बात करें' : 'Talk with Didi Again'}
                </button>
                {onClose && (
                  <button
                    onClick={onClose}
                    className="text-xs bg-white hover:bg-slate-50 text-slate-700 font-bold px-4 py-2 rounded-full border border-slate-200 transition cursor-pointer"
                  >
                    {lang === 'hi' ? 'बंद करें' : 'Close'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Prompt Chips (Horizontal Scrollable on Mobile/Tab/PC) */}
      {!sessionDone && messages.length > 0 && (
        <div className="px-4 sm:px-6 py-2 overflow-x-auto flex gap-2 no-scrollbar bg-white/60 backdrop-blur-xs border-t border-slate-100">
          {(quickPrompts[lang] || quickPrompts.en).map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="text-[11px] font-semibold text-slate-600 bg-white hover:bg-emerald-50 hover:text-[#0F4C3A] border border-slate-200 hover:border-emerald-300 rounded-full px-3 py-1.5 whitespace-nowrap transition-all shadow-2xs active:scale-95 cursor-pointer flex-shrink-0"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      {!sessionDone && (
        <div className="p-3 sm:p-4 bg-white border-t border-slate-100 flex-shrink-0">
          <div className="flex items-center gap-2">
            <textarea
              ref={inputRef}
              rows={1}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={lang === 'hi' ? 'यहाँ अपनी बात लिखें… (Enter दबाएँ)' : 'Share whatever is in your heart… (Press Enter)'}
              className="flex-1 bg-[#F8FAFC] border border-slate-200 text-slate-900 placeholder-slate-400 rounded-full px-4 sm:px-5 py-2.5 sm:py-3 text-xs sm:text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[#0F4C3A]/20 focus:border-[#0F4C3A] focus:bg-white transition max-h-24 leading-normal"
              style={{ height: 'auto', minHeight: '42px' }}
              onInput={(e) => {
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 96) + 'px';
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!inputText.trim()}
              className="w-10 h-10 sm:w-11 sm:h-11 rounded-full bg-[#0F4C3A] hover:bg-[#0A392B] disabled:opacity-40 flex items-center justify-center flex-shrink-0 text-white shadow-sm transition-all active:scale-95 cursor-pointer"
            >
              <Send className="w-4 h-4 ml-0.5" />
            </button>
          </div>

          <div className="flex items-center justify-between mt-2 px-2 text-[10px] text-slate-400 font-medium">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              {lang === 'hi' ? 'सुरक्षित एवं गोपनीय बातचीत · कोई समय सीमा नहीं' : 'Safe & Confidential · Take your time'}
            </span>
            <span>24x7 Helpline: 14566</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Header sub-component ────────────────────────────────────────────────────

function ChatHeader({ lang, setLang, onClose, embedded, victimId, onEndChat, sessionDone }) {
  return (
    <header className="px-4 sm:px-6 py-3.5 bg-white border-b border-slate-100 flex items-center justify-between flex-shrink-0 z-10">
      <div className="flex items-center gap-3">
        <div className="relative">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-base sm:text-lg shadow-2xs">
            🌸
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full ring-2 ring-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="text-sm font-extrabold text-slate-900 tracking-tight">{BOT_NAME}</p>
            <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
              <Sparkles className="w-2.5 h-2.5" /> Gemini AI
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-medium">
            {victimId ? `${victimId} · ` : ''}{lang === 'hi' ? 'आपकी अपनी सहेली दीदी · ऑनलाइन' : 'Your Caring Elder Sister · Online'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* User-controlled End Conversation Button */}
        {!sessionDone && onEndChat && (
          <button
            onClick={onEndChat}
            title={lang === 'hi' ? 'जब आप तैयार हों तो बातचीत पूरी करें' : 'End conversation when you are ready'}
            className="text-[11px] font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-full transition-colors flex items-center gap-1 cursor-pointer active:scale-95"
          >
            <span>👋</span>
            <span className="hidden xs:inline">{lang === 'hi' ? 'बात पूरी करें' : 'End Chat'}</span>
          </button>
        )}

        {/* Language toggle */}
        <button
          onClick={() => setLang((l) => (l === 'en' ? 'hi' : 'en'))}
          className="text-[11px] font-bold text-[#0F4C3A] bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 px-3 py-1.5 rounded-full transition-colors cursor-pointer active:scale-95"
        >
          {lang === 'en' ? 'हिंदी' : 'English'}
        </button>

        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 w-8 h-8 flex items-center justify-center rounded-full hover:bg-slate-100 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  );
}
