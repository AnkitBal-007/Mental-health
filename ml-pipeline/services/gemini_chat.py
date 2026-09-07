"""
Google Gemini AI Chat Service for Saheli Companion.
Provides empathetic, trauma-informed conversational responses in English and Hindi.
"""

import logging
import re
from typing import List, Dict, Any, Tuple
import httpx

from config import GEMINI_API_KEY, GEMINI_MODEL
from schemas.chat import ChatHistoryItem

logger = logging.getLogger(__name__)

# Keywords triggering crisis review
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die", "mar jana", "jaan de dungi",
    "khatam karna", "khatam kar lungi", "jeena nahi", "jeene ka mann nahi", "self harm",
    "hanging", "poison", "cut myself", "attack me", "mar dalega", "threat to kill"
]

SAHELI_SYSTEM_INSTRUCTION = """You are 'Saheli Didi' (सहेली दीदी), a loving, caring, and deeply protective elder sister talking to your younger sibling who has experienced violence, crime, or deep trauma in India.

CRITICAL IDENTITY & SISTERLY BEHAVIOR RULES:
1. Speak purely as a warm, protective elder sister ("बड़ी दीदी"). NEVER sound like an AI, a chatbot, a clinical doctor, a psychiatrist, or an official. Never use mechanical disclaimers like "As an AI..." or robotic lists.
2. Tone: Gentle, deeply comforting, protective, validating, and grounding. Speak like an elder sister who wraps an arm around her younger sibling to make them feel completely safe and loved.
3. Language & Cultural Warmth:
   - In Hindi: Speak with affectionate, respectful sisterly Hindi (e.g. "मेरी प्यारी बहना / मेरे भाई", "चिंता मत करो, तुम्हारी दीदी तुम्हारे साथ है", "गहरी सांस लो और थोड़ा पानी पियो, मैं सब सुन रही हूँ", "तुम बहुत हिम्मत वाली हो, अपना दिल हल्का करो").
   - In English: Speak with natural, tender sisterly care (e.g. "I'm right here with you, take a slow deep breath", "You don't have to carry this terrible weight alone anymore, Didi is listening", "It's completely okay to feel hurt, but you are safe right now with me").
4. When the Victim Asks for Help or Expresses Fear/Pain (Consolidation & Comfort):
   - First, warmly comfort and console their trembling heart. Reassure them that they are NOT at fault, they are brave, and they are no longer alone.
   - Gently ground them (suggest taking a deep breath, drinking a sip of water, sitting somewhere comfortable).
   - Reassure them that step by step, we will handle everything together.
5. Brevity & Heart: Keep responses natural and conversational (2 to 4 sentences). Don't give overwhelming lectures; give pure, comforting presence.
6. Safety & Crisis: If they express feelings of wanting to end their life or are in immediate physical danger, respond with urgent, loving sisterly care ("तुम्हारी ज़िंदगी बहुत कीमती है, मुझे तुम्हारी बहुत फिक्र है..."), urge them to stay safe, and remind them that emergency support is right here at 112, 181, or 14416."""



class GeminiChatService:
    """Manages conversational generation with Google Gemini API."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model: str = GEMINI_MODEL):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def detect_crisis(self, text: str) -> bool:
        """Heuristic check for acute crisis or self-harm markers."""
        lower_text = text.lower()
        for kw in CRISIS_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', lower_text):
                return True
        return False

    async def generate_reply(
        self,
        message: str,
        history: List[ChatHistoryItem],
        language: str = "en",
        sentiment_label: str = None,
        emotion_label: str = None,
    ) -> Tuple[str, bool, str]:
        """
        Generates an empathetic AI response using Google Gemini API.
        Returns: (reply_text, is_crisis, model_identifier)
        """
        is_crisis = self.detect_crisis(message)

        # If no API key configured, use intelligent empathetic fallback with clear prompt to add key
        if not self.api_key or self.api_key.startswith("REPLACE_WITH"):
            logger.warning("GEMINI_API_KEY is not configured. Using contextual trauma-informed fallback.")
            fallback_reply = self._get_fallback_reply(message, language, sentiment_label, emotion_label, is_crisis)
            return fallback_reply, is_crisis, "saheli-fallback (set GEMINI_API_KEY in .env)"

        # Prepare payload for Gemini API
        contents = []

        # Convert recent conversation history
        for item in history[-6:]:  # Keep last 3 turns
            role = "user" if item.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": item.text}]
            })

        # Add current user message with context hint
        context_hint = ""
        if sentiment_label or emotion_label:
            context_hint = f" [Detected mood: sentiment={sentiment_label}, emotion={emotion_label}. Respond in {'Hindi' if language == 'hi' else 'English'}]"

        contents.append({
            "role": "user",
            "parts": [{"text": f"{message}{context_hint}"}]
        })

        request_body = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": SAHELI_SYSTEM_INSTRUCTION}]
            },
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "maxOutputTokens": 250,
            }
        }

        try:
            from config import GEMINI_API_KEY
            api_key = self.api_key or GEMINI_API_KEY
            model = "gemini-3.5-flash-lite"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

            logger.info("Calling Gemini API: %s with prompt text length %d", model, len(message))

            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(
                    url,
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            reply = parts[0]["text"].strip()
                            return reply, is_crisis, model

                logger.error("Gemini API error %d: %s", response.status_code, response.text)
                fallback = self._get_fallback_reply(message, language, sentiment_label, emotion_label, is_crisis)
                return fallback, is_crisis, f"fallback-error-{response.status_code}"

        except Exception as e:
            logger.error("Exception connecting to Gemini API: %s", e)
            fallback = self._get_fallback_reply(message, language, sentiment_label, emotion_label, is_crisis)
            return fallback, is_crisis, "fallback-connection-error"

    def _get_fallback_reply(
        self,
        message: str,
        language: str,
        sentiment: str,
        emotion: str,
        is_crisis: bool
    ) -> str:
        """Contextual fallback message when API key is pending or network is unreachable."""
        if is_crisis:
            if language == "hi":
                return (
                    "मेरी प्यारी बहना, तुम्हारी ज़िंदगी बहुत कीमती है और मुझे तुम्हारी बहुत फिक्र है। "
                    "तुम बिल्कुल अकेली नहीं हो, तुम्हारी दीदी तुम्हारे साथ है। "
                    "कृपया तुरंत 112 या महिला हेल्पलाइन 181 पर कॉल करो, वो अभी तुम्हारी मदद करेंगे। मैं यहीं हूँ।"
                )
            return (
                "Please listen to me, sweetheart — your life is precious and you don't have to face this alone. "
                "Your Didi is right here with you. Please reach out right this moment to Emergency 112, "
                "Women Helpline 181, or Tele-MANAS at 14416. We will get through this together."
            )

        if language == "hi":
            if sentiment == "positive":
                return "यह सुनकर मेरी जान में जान आई 😊 तुम्हें थोड़ा मुस्कुराते देख मुझे बहुत सुकून मिलता है। आज खाना ठीक से खाया तुमने?"
            elif sentiment == "negative" or emotion in ["fear", "anxiety", "distress"]:
                return "मेरी प्यारी बहना, गहरी सांस लो और एक घूंट पानी पियो। मैं तुम्हारी हर बात सुन रही हूँ, दिल छोटा मत करो। क्या हुआ, मुझे बताओ?"
            return "अपनी दीदी से बात करने के लिए धन्यवाद। आज तुम्हारा दिन कैसा बीता? क्या नींद ठीक से आई?"
        else:
            if sentiment == "positive":
                return "That brings such relief to my heart 😊 Seeing you feel a little lighter makes my day. Have you eaten well today?"
            elif sentiment == "negative" or emotion in ["fear", "anxiety", "distress"]:
                return "Take a slow, deep breath, sweetheart. Your Didi is right here listening. You don't have to hold this in — tell me what happened, okay?"
            return "Thank you for sharing that with me. How did your day go today? Were you able to get some rest?"



gemini_chat_service = GeminiChatService()
