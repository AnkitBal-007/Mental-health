"""
FastAPI Router for AI Chatbot conversational interactions & real-time text analysis.
Provides Gemini AI Elder Sister ("Saheli Didi") conversations and psychological risk detection.
"""

import logging
import json
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


async def analyze_text_with_gemini(text: str, language: str = "en") -> Optional[Dict[str, Any]]:
    """Use Gemini AI to extract distress score, risk level, threat detection, and risk factors."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key or gemini_key.startswith("REPLACE_WITH"):
        return None

    prompt = (
        "You are an expert clinical crisis & trauma evaluation AI in a victim protection system in India. "
        "Analyze this citizen check-in message in English or Hindi:\n"
        f'"{text}"\n\n'
        "Evaluate psychological distress, risk level, acute danger/threats, and emotion accurately.\n"
        "Return ONLY a valid JSON object matching this structure:\n"
        "{\n"
        '  "sentiment": "negative" | "positive" | "neutral",\n'
        '  "confidence": float between 0.0 and 1.0,\n'
        '  "emotion": "fear" | "anxiety" | "distress" | "sadness" | "anger" | "calm" | "hope" | "neutral",\n'
        '  "distress_score": float between 0.0 and 100.0,\n'
        '  "risk_level": "critical" | "high" | "moderate" | "low",\n'
        '  "threat_detected": boolean,\n'
        '  "risk_factors": ["string describing specific risk factor, e.g. Threat to Life, Witness Intimidation, Sleep Disturbance, Stalking, Appetite Loss, Acute Panic"]\n'
        "}"
    )

    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
    for model in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            parsed = json.loads(parts[0]["text"].strip())
                            score = float(parsed.get("distress_score", 50.0))
                            if score <= 1.0 and score > 0:
                                score = score * 100.0

                            sent_label = parsed.get("sentiment", "neutral")
                            conf = float(parsed.get("confidence", 0.9))
                            primary_emo = parsed.get("emotion", "neutral")
                            is_threat = bool(parsed.get("threat_detected", False)) or detect_crisis(text)
                            r_level = parsed.get("risk_level", "critical" if is_threat else ("high" if score >= 65 else ("moderate" if score >= 40 else "low")))
                            r_factors = parsed.get("risk_factors", [])

                            return {
                                "sentiment": {"label": sent_label, "confidence": round(conf, 2)},
                                "emotions": [{"label": primary_emo, "score": round(conf, 2)}],
                                "distress_score": round(score, 1),
                                "risk_level": r_level,
                                "threat_detected": is_threat,
                                "risk_factors": r_factors,
                                "language": language,
                                "text_length": len(text),
                                "model_used": model,
                            }
        except Exception as e:
            logger.warning("Gemini risk analysis error with %s: %s", model, e)
            continue
    return None


def analyze_text_lexicon(text: str, language: str = "en") -> Dict[str, Any]:
    """Rich clinical rule-based sentiment, emotion, and risk factor detection."""
    lower = text.lower()
    words = re.findall(r'\b\w+\b', lower)

    pos_count = sum(1 for w in words if w in POSITIVE_TERMS)
    neg_count = sum(1 for w in words if w in NEGATIVE_TERMS)

    is_threat = detect_crisis(text)
    has_somatic = detect_somatic_distress(text)

    # Check for specific emotional domains
    is_anxious = any(w in lower for w in ["anxious", "anxiety", "panic", "ghabrahat", "chinta", "nervous", "bechaini"])
    is_fear = any(w in lower for w in ["afraid", "scared", "fear", "threat", "dar", "darr", "danger", "khauf", "khatra"])
    is_sad = any(w in lower for w in ["sad", "depressed", "hopeless", "crying", "tears", "udas", "rona", "dukhi"])
    is_insomnia = any(w in lower for w in ["sleep", "sleepless", "nightmare", "eating", "eat", "appetite", "neend", "bhukh", "khana"])

    risk_factors = []
    if is_threat:
        risk_factors.append("Threat / Physical Danger")
    if is_fear:
        risk_factors.append("Acute Fear / Intimidation")
    if is_anxious:
        risk_factors.append("Severe Anxiety / Panic")
    if is_insomnia:
        risk_factors.append("Sleep / Appetite Disturbance")
    if is_sad:
        risk_factors.append("Psychological Trauma / Hopelessness")

    if is_threat:
        label = "negative"
        conf = 0.95
        primary_emo = "fear"
        distress_score = 90.0
        risk_level = "critical"
    elif is_fear or (is_anxious and has_somatic):
        label = "negative"
        conf = 0.90
        primary_emo = "fear" if is_fear else "anxiety"
        distress_score = 78.0
        risk_level = "high"
    elif is_anxious or is_sad or has_somatic or neg_count > 0:
        label = "negative"
        conf = min(0.95, 0.65 + neg_count * 0.10)
        primary_emo = "anxiety" if is_anxious else ("sadness" if is_sad else "distress")
        distress_score = min(72.0, 52.0 + neg_count * 8.0)
        risk_level = "high" if distress_score >= 65 else "moderate"
    elif pos_count > neg_count:
        label = "positive"
        conf = min(0.95, 0.70 + pos_count * 0.10)
        primary_emo = "calm"
        distress_score = max(12.0, 32.0 - pos_count * 6.0)
        risk_level = "low"
    else:
        label = "neutral"
        conf = 0.60
        primary_emo = "neutral"
        distress_score = 45.0
        risk_level = "moderate"

    emotions = [
        {"label": primary_emo, "score": round(conf, 2)},
        {"label": "anxiety" if primary_emo != "anxiety" else "fear", "score": 0.20},
        {"label": "calm" if primary_emo != "calm" else "neutral", "score": 0.10},
    ]

    return {
        "sentiment": {"label": label, "confidence": round(conf, 2)},
        "emotions": emotions,
        "distress_score": round(distress_score, 1),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "language": language,
        "text_length": len(text),
        "threat_detected": is_threat,
        "somatic_distress": has_somatic,
        "model_used": "clinical-lexicon-v2",
    }


@router.post("/analyze/text")
async def analyze_text_endpoint(req: TextAnalysisRequest):
    """Analyze sentiment, emotion, distress score, and risk factors in real time."""
    # 1. Try Gemini Clinical Crisis & Risk Factor Analysis
    gemini_res = await analyze_text_with_gemini(req.text, req.language)
    if gemini_res:
        return gemini_res

    # 2. High-accuracy Lexicon Fallback
    return analyze_text_lexicon(req.text, req.language)


@router.post("/chat/respond", response_model=ChatResponse)
async def generate_chat_response(req: ChatRequest):
    """Generates an empathetic AI sister response using Gemini AI or contextual fallback."""
    is_crisis = detect_crisis(req.message)
    detected_lang = detect_language(req.message)
    target_lang = detected_lang if detected_lang else req.language

    # Auto-extract mood and risk factor
    quick_analysis = await analyze_text_with_gemini(req.message, target_lang)
    if not quick_analysis:
        quick_analysis = analyze_text_lexicon(req.message, target_lang)

    sentiment = req.sentiment_label or quick_analysis.get("sentiment", {}).get("label")
    emotion = req.emotion_label or quick_analysis.get("emotions", [{}])[0].get("label")
    risk_factors = quick_analysis.get("risk_factors", [])
    risk_level = quick_analysis.get("risk_level", "low")

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    # If Gemini API Key is available, call Google Gemini with risk context
    if gemini_key and not gemini_key.startswith("REPLACE_WITH"):
        models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
        for model in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"

                contents = []
                for item in req.history[-6:]:
                    role = "user" if item.role == "user" else "model"
                    contents.append({"role": role, "parts": [{"text": item.text}]})

                lang_instruction = "Respond in natural English" if target_lang == "en" else "Respond in warm sisterly Hindi"
                context_str = f"Mood: {sentiment}, Emotion: {emotion}, Risk Level: {risk_level}"
                if risk_factors:
                    context_str += f", Risk Factors: {', '.join(risk_factors)}"

                contents.append({
                    "role": "user",
                    "parts": [{"text": f"{req.message}\n[Instruction: {lang_instruction}. Clinical Context: {context_str}]"}]
                })

                payload = {
                    "contents": contents,
                    "systemInstruction": {"parts": [{"text": SAHELI_SYSTEM_INSTRUCTION}]},
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 250},
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                return ChatResponse(
                                    reply=parts[0]["text"].strip(),
                                    crisis_flag=is_crisis or quick_analysis.get("threat_detected", False),
                                    language=target_lang,
                                    model_used=model,
                                )
            except Exception as e:
                logger.warning("Gemini generation error with %s: %s", model, e)
                continue

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
