"""
FastAPI Router for AI Chatbot conversational interactions & real-time text analysis.
Provides Gemini AI Elder Sister ("Saheli Didi") conversations and psychological risk detection.
"""

import logging
import os
import re
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Chatbot & Threat Detection"])

# Threat & Acute Crisis Keywords
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die", "mar jana", "jaan de dungi",
    "khatam karna", "khatam kar lungi", "jeena nahi", "jeene ka mann nahi", "self harm",
    "hanging", "poison", "cut myself", "attack me", "mar dalega", "threat to kill",
    "threat", "threatening", "beat me", "abuse", "danger", "darr lag raha hai", "bachao",
    "dhamki", "chaku", "marne ki", "maar dalenge", "kidnap", "gun", "knife"
]

# Psychosomatic Distress & Trauma Indicators (Insomnia, Appetite Loss, Panic, Depression)
DISTRESS_SYMPTOMS = {
    # Insomnia / Sleep disturbances
    "cant sleep", "cannot sleep", "unable to sleep", "sleep at night", "sleepless", "nightmare",
    "nightmares", "bad dreams", "waking up", "insomnia", "neend nahi", "neend nhi", "so nahi",
    # Appetite & Somatic disturbances
    "eating", "dont feel like eating", "not eating", "lost appetite", "no appetite", "cant eat",
    "cannot eat", "khana nahi", "bhukh nahi", "khaya nahi", "kamzor", "kamzori", "weakness",
    "shivering", "trembling", "headache", "chest pain", "choking", "vomit", "ultee",
    # Psychological pain & Trauma
    "hopeless", "worthless", "tired of life", "crying every day", "cant stop crying", "breakdown",
    "panic attack", "scared to go out", "paranoia", "following me", "stalking", "flashbacks",
    "akela pan", "rona aa raha", "ghabrahat", "bechaini", "dar lag raha", "takleef ho rahi"
}

POSITIVE_TERMS = {
    "good", "great", "better", "best", "relieved", "happy", "safe", "calm", "peaceful", "hope",
    "thank", "thanks", "supported", "comfortable", "healing", "strong", "improving", "fine", "okay",
    "theek", "shant", "behtar", "acha", "accha", "khush", "sukoon", "shanti", "himmat", "surakshit",
    "rahat", "smile", "smiling", "improved", "blessed", "relaxed"
}

NEGATIVE_TERMS = {
    "bad", "terrible", "worst", "hopeless", "sad", "unhappy", "depressed", "afraid", "scared",
    "fear", "threat", "pain", "hurt", "crying", "anxious", "anxiety", "panic", "suicide", "dying",
    "alone", "helpless", "unsafe", "danger", "trauma", "nightmare", "dard", "takleef", "dar", "khauf",
    "chinta", "pareshaan", "pareshan", "akela", "khatra", "marna", "gham", "rona", "udaas",
    "exhausted", "tired", "weak", "heavy", "broken", "numb", "angry", "furious", "lost", "struggling"
}

SAHELI_SYSTEM_INSTRUCTION = """You are 'Saheli Didi' (सहेली दीदी), a loving, caring, and deeply protective elder sister talking to your younger sibling who has experienced violence, crime, or deep trauma in India.

CRITICAL SISTERLY RULES:
1. STRICT LANGUAGE MATCHING:
   - If the user writes in English, reply in English with natural, tender sisterly care.
   - If the user writes in Hindi or Hinglish, reply in warm, affectionate Hindi ("मेरी प्यारी बहना / मेरे भाई").
2. Validate their emotional state immediately (e.g. if they mention trouble sleeping or eating, validate how trauma affects the body, offer gentle grounding like drinking warm water, and encourage them).
3. Brevity & Warmth: Keep responses concise (2 to 4 sentences). Speak purely as a protective elder sister, NEVER clinical or robotic.
4. If immediate physical danger or suicidal intent is mentioned, show urgent protective love and remind them of Emergency 112, Women Helpline 181, or Tele-MANAS 14416."""


class ChatHistoryItem(BaseModel):
    role: str
    text: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatHistoryItem]] = Field(default_factory=list)
    language: str = "en"
    sentiment_label: Optional[str] = None
    emotion_label: Optional[str] = None
    victim_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    crisis_flag: bool
    language: str
    model_used: str


class TextAnalysisRequest(BaseModel):
    text: str
    language: str = "en"


def detect_crisis(text: str) -> bool:
    """Detect acute crisis or physical danger signals."""
    lower = text.lower()
    for kw in CRISIS_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', lower) or kw in lower:
            return True
    return False


def detect_somatic_distress(text: str) -> bool:
    """Detect somatic symptoms like insomnia, appetite loss, trauma flashbacks."""
    lower = text.lower()
    for sym in DISTRESS_SYMPTOMS:
        if sym in lower:
            return True
    return False


def detect_language(text: str) -> str:
    """Detects whether user is speaking Hindi (Devanagari or Romanized) vs English."""
    if re.search(r'[\u0900-\u097F]', text):
        return "hi"
    hindi_keywords = ["mujhe", "mera", "meri", "kya", "hai", "hain", "nahi", "darr", "dar", "takleef", "chinta", "karo", "karna", "didi", "bhai", "bahana", "aap", "tum", "khana", "neend"]
    words = text.lower().split()
    if any(w in hindi_keywords for w in words):
        return "hi"
    return "en"


def analyze_text_lexicon(text: str, language: str = "en") -> Dict[str, Any]:
    """Rich clinical rule-based sentiment and emotion analysis."""
    lower = text.lower()
    words = re.findall(r'\b\w+\b', lower)

    pos_count = sum(1 for w in words if w in POSITIVE_TERMS)
    neg_count = sum(1 for w in words if w in NEGATIVE_TERMS)

    is_threat = detect_crisis(text)
    has_somatic = detect_somatic_distress(text)

    # Check for specific emotional domains
    is_anxious = any(w in lower for w in ["anxious", "anxiety", "panic", "ghabrahat", "chinta", "nervous"])
    is_fear = any(w in lower for w in ["afraid", "scared", "fear", "threat", "dar", "darr", "danger"])
    is_sad = any(w in lower for w in ["sad", "depressed", "hopeless", "crying", "tears", "udas", "rona"])
    is_insomnia = any(w in lower for w in ["sleep", "eating", "eat", "appetite", "neend", "bhukh"])

    if is_threat or has_somatic or neg_count > 0:
        label = "negative"
        conf = 0.90 if (is_threat or has_somatic) else min(0.95, 0.60 + neg_count * 0.15)
        
        primary_emo = "distress"
        if is_threat or is_fear:
            primary_emo = "fear"
        elif is_anxious:
            primary_emo = "anxiety"
        elif is_insomnia or has_somatic:
            primary_emo = "distress"
        elif is_sad:
            primary_emo = "sadness"

        emotions = [
            {"label": primary_emo, "score": round(conf, 4)},
            {"label": "anxiety" if primary_emo != "anxiety" else "fear", "score": 0.20},
            {"label": "neutral", "score": 0.05},
        ]
    elif pos_count > neg_count:
        label = "positive"
        conf = min(0.95, 0.60 + pos_count * 0.15)
        emotions = [
            {"label": "calm", "score": round(conf, 4)},
            {"label": "hope", "score": 0.25},
            {"label": "neutral", "score": 0.05},
        ]
    else:
        label = "neutral"
        conf = 0.55
        emotions = [
            {"label": "neutral", "score": 0.55},
            {"label": "calm", "score": 0.25},
            {"label": "anxiety", "score": 0.20},
        ]

    return {
        "sentiment": {"label": label, "confidence": round(conf, 4)},
        "emotions": emotions,
        "language": language,
        "text_length": len(text),
        "threat_detected": is_threat,
        "somatic_distress": has_somatic,
    }


@router.post("/analyze/text")
async def analyze_text_endpoint(req: TextAnalysisRequest):
    """Analyze sentiment, emotion, and threat indicators in text."""
    # Attempt ML pipeline if accessible
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.post(f"{ML_PIPELINE_URL}/analyze/text", json=req.model_dump())
            if res.status_code == 200:
                data = res.json()
                data["threat_detected"] = detect_crisis(req.text)
                return data
    except Exception:
        pass

    # High-accuracy fallback
    return analyze_text_lexicon(req.text, req.language)


@router.post("/chat/respond", response_model=ChatResponse)
async def generate_chat_response(req: ChatRequest):
    """Generates an empathetic AI sister response using Gemini AI or contextual fallback."""
    is_crisis = detect_crisis(req.message)
    detected_lang = detect_language(req.message)
    target_lang = detected_lang if detected_lang else req.language

    # Auto-extract mood if not provided
    quick_analysis = analyze_text_lexicon(req.message, target_lang)
    sentiment = req.sentiment_label or quick_analysis.get("sentiment", {}).get("label")
    emotion = req.emotion_label or quick_analysis.get("emotions", [{}])[0].get("label")

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    # If Gemini API Key is available, call Google Gemini
    if gemini_key and not gemini_key.startswith("REPLACE_WITH"):
        try:
            model = "gemini-3.5-flash-lite"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"

            contents = []
            for item in req.history[-6:]:
                role = "user" if item.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": item.text}]})

            lang_instruction = "Respond in natural English" if target_lang == "en" else "Respond in warm sisterly Hindi"
            contents.append({
                "role": "user",
                "parts": [{"text": f"{req.message}\n[Instruction: {lang_instruction}. Mood detected: {sentiment}, emotion: {emotion}]"}]
            })

            payload = {
                "contents": contents,
                "systemInstruction": {"parts": [{"text": SAHELI_SYSTEM_INSTRUCTION}]},
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 250},
            }

            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            return ChatResponse(
                                reply=parts[0]["text"].strip(),
                                crisis_flag=is_crisis,
                                language=target_lang,
                                model_used="gemini-3.5-flash-lite",
                            )
        except Exception as e:
            logger.warning("Gemini direct generation error: %s", e)

    # Contextual Trauma-Informed Fallback matching language
    if is_crisis:
        if target_lang == "hi":
            reply = (
                "मेरी प्यारी बहना, तुम्हारी ज़िंदगी बहुत कीमती है और मुझे तुम्हारी बहुत फिक्र है। "
                "तुम बिल्कुल अकेली नहीं हो, तुम्हारी दीदी तुम्हारे साथ है। "
                "कृपया तुरंत 112 या महिला हेल्पलाइन 181 पर कॉल करो, वो अभी तुम्हारी मदद करेंगे।"
            )
        else:
            reply = (
                "Please listen to me, sweetheart — your life is precious and you don't have to face this alone. "
                "Your Didi is right here with you. Please reach out right this moment to Emergency 112, "
                "Women Helpline 181, or Tele-MANAS at 14416."
            )
    else:
        if target_lang == "hi":
            if sentiment == "positive":
                reply = "यह सुनकर मेरी जान में जान आई 😊 तुम्हें थोड़ा मुस्कुराते देख मुझे बहुत सुकून मिलता है। आज खाना ठीक से खाया तुमने?"
            elif emotion == "distress" or "sleep" in req.message or "neend" in req.message or "khana" in req.message:
                reply = "मेरी प्यारी बहना, जब मन पर इतना बोझ होता है तो भूख और नींद उड़ जाना बहुत स्वाभाविक है। थोड़ा गुनगुना पानी पियो, मैं तुम्हारे पास ही हूँ। अपना दिल हल्का करो।"
            elif sentiment == "negative" or emotion in ["fear", "anxiety"]:
                reply = "मेरी प्यारी बहना, गहरी सांस लो और एक घूंट पानी पियो। मैं तुम्हारी हर बात सुन रही हूँ, दिल छोटा मत करो। क्या हुआ, मुझे बताओ?"
            else:
                reply = "अपनी दीदी से बात करने के लिए धन्यवाद। आज तुम्हारा दिन कैसा बीता? क्या नींद ठीक से आई?"
        else:
            if sentiment == "positive":
                reply = "That brings such relief to my heart 😊 Seeing you feel a little lighter makes my day. Have you eaten well today?"
            elif emotion == "distress" or "sleep" in req.message or "eating" in req.message or "eat" in req.message:
                reply = "It breaks my heart to hear you're going through this, sweetheart. When we carry deep stress, our body struggles to rest and eat. Take a slow sip of warm water, take a deep breath — Didi is right here with you."
            elif sentiment == "negative" or emotion in ["fear", "anxiety"]:
                reply = "Take a slow, deep breath, sweetheart. Your Didi is right here listening. You don't have to hold this in — tell me what happened, okay?"
            else:
                reply = "Thank you for sharing that with me. How did your day go today? Were you able to get some rest?"

    return ChatResponse(
        reply=reply,
        crisis_flag=is_crisis,
        language=target_lang,
        model_used="saheli-companion-core",
    )
