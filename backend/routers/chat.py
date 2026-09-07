"""
FastAPI Router for AI Chatbot conversational interactions & real-time text analysis.
Provides Gemini AI Elder Sister ("Saheli Didi") conversations and crisis threat detection.
"""

import logging
import os
import re
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import httpx

from config import ML_PIPELINE_URL

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Chatbot & Threat Detection"])

# Threat & Crisis Keywords
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die", "mar jana", "jaan de dungi",
    "khatam karna", "khatam kar lungi", "jeena nahi", "jeene ka mann nahi", "self harm",
    "hanging", "poison", "cut myself", "attack me", "mar dalega", "threat to kill",
    "threat", "threatening", "beat me", "abuse", "danger", "darr lag raha hai", "bachao"
]

POSITIVE_TERMS = {
    "good", "great", "better", "best", "relieved", "happy", "safe", "calm", "peaceful", "hope",
    "thank", "thanks", "supported", "comfortable", "healing", "strong", "improving", "fine", "okay",
    "theek", "shant", "behtar", "acha", "accha", "khush", "sukoon", "shanti", "himmat", "surakshit"
}

NEGATIVE_TERMS = {
    "bad", "terrible", "worst", "hopeless", "sad", "unhappy", "depressed", "afraid", "scared",
    "fear", "threat", "pain", "hurt", "crying", "anxious", "anxiety", "panic", "suicide", "dying",
    "alone", "helpless", "unsafe", "danger", "trauma", "nightmare", "dard", "takleef", "dar", "khauf",
    "chinta", "pareshaan", "pareshan", "akela", "khatra", "marna", "gham", "rona", "udaas"
}

SAHELI_SYSTEM_INSTRUCTION = """You are 'Saheli Didi' (सहेली दीदी), a loving, caring, and deeply protective elder sister talking to your younger sibling who has experienced violence, crime, or deep trauma in India.

CRITICAL SISTERLY BEHAVIOR RULES:
1. Speak purely as a warm, protective elder sister ("बड़ी दीदी"). Never sound clinical or robotic.
2. In Hindi: Speak with affectionate, respectful sisterly Hindi (e.g. "मेरी प्यारी बहना / मेरे भाई", "चिंता मत करो, तुम्हारी दीदी तुम्हारे साथ है", "गहरी सांस लो और थोड़ा पानी पियो").
3. In English: Speak with natural, tender sisterly care (e.g. "I'm right here with you, take a slow deep breath", "You don't have to carry this alone, Didi is listening").
4. Keep responses natural and conversational (2 to 4 sentences).
5. If immediate physical danger or self-harm is mentioned, offer urgent comforting care and remind them of Emergency 112, Women Helpline 181, or Tele-MANAS 14416."""


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


def analyze_text_lexicon(text: str, language: str = "en"):
    """Quick rule-based text sentiment and emotion analysis."""
    lower = text.lower()
    words = re.findall(r'\b\w+\b', lower)

    pos_count = sum(1 for w in words if w in POSITIVE_TERMS)
    neg_count = sum(1 for w in words if w in NEGATIVE_TERMS)

    is_threat = detect_crisis(text)

    if is_threat or neg_count > pos_count:
        label = "negative"
        conf = 0.85 if is_threat else min(0.95, 0.50 + neg_count * 0.15)
        emotions = [
            {"label": "fear" if is_threat else "distress", "score": conf},
            {"label": "anxiety", "score": 0.20},
            {"label": "neutral", "score": 0.10},
        ]
    elif pos_count > neg_count:
        label = "positive"
        conf = min(0.95, 0.50 + pos_count * 0.15)
        emotions = [
            {"label": "calm", "score": conf},
            {"label": "hope", "score": 0.20},
            {"label": "neutral", "score": 0.10},
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

    # Fallback to backend lexical analyzer
    return analyze_text_lexicon(req.text, req.language)


@router.post("/chat/respond", response_model=ChatResponse)
async def generate_chat_response(req: ChatRequest):
    """Generates an empathetic AI sister response using Gemini AI or contextual fallback."""
    is_crisis = detect_crisis(req.message)
    
    # Auto-extract mood if not provided
    sentiment = req.sentiment_label
    emotion = req.emotion_label
    if not sentiment or not emotion:
        quick_analysis = analyze_text_lexicon(req.message, req.language)
        sentiment = sentiment or quick_analysis.get("sentiment", {}).get("label")
        emotion = emotion or quick_analysis.get("emotions", [{}])[0].get("label")

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

            contents.append({
                "role": "user",
                "parts": [{"text": req.message}]
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
                                crisis_flag=is_crisis,
                                language=req.language,
                                model_used="gemini-3.5-flash-lite",
                            )
        except Exception as e:
            logger.warning("Gemini direct generation error: %s", e)

    # Contextual Trauma-Informed Fallback
    if is_crisis:
        if req.language == "hi":
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
        if req.language == "hi":
            if sentiment == "positive":
                reply = "यह सुनकर मेरी जान में जान आई 😊 तुम्हें थोड़ा मुस्कुराते देख मुझे बहुत सुकून मिलता है। आज खाना ठीक से खाया तुमने?"
            elif sentiment == "negative" or emotion in ["fear", "anxiety", "distress"]:
                reply = "मेरी प्यारी बहना, गहरी सांस लो और एक घूंट पानी पियो। मैं तुम्हारी हर बात सुन रही हूँ, दिल छोटा मत करो। क्या हुआ, मुझे बताओ?"
            else:
                reply = "अपनी दीदी से बात करने के लिए धन्यवाद। आज तुम्हारा दिन कैसा बीता? क्या नींद ठीक से आई?"
        else:
            if sentiment == "positive":
                reply = "That brings such relief to my heart 😊 Seeing you feel a little lighter makes my day. Have you eaten well today?"
            elif sentiment == "negative" or emotion in ["fear", "anxiety", "distress"]:
                reply = "Take a slow, deep breath, sweetheart. Your Didi is right here listening. You don't have to hold this in — tell me what happened, okay?"
            else:
                reply = "Thank you for sharing that with me. How did your day go today? Were you able to get some rest?"

    return ChatResponse(
        reply=reply,
        crisis_flag=is_crisis,
        language=req.language,
        model_used="saheli-companion-core",
    )
