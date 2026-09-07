"""
Text analysis service — Fast, lightweight multilingual sentiment + emotion classification.
Designed for low-memory cloud instances (Render Free Tier: < 50MB RAM).

Supports English and Hindi text using an emotional lexicon + semantic valence scoring.
"""

import logging
import re
from typing import Dict, List

from config import EMOTION_LABELS

logger = logging.getLogger(__name__)

# Multilingual Sentiment & Emotion Lexicons
POSITIVE_TERMS = {
    # English
    "good", "great", "better", "best", "relieved", "happy", "safe", "calm", "peaceful", "hope",
    "thank", "thanks", "supported", "comfortable", "healing", "strong", "improving", "fine",
    "okay", "relaxed", "glad", "blessed", "wonderful", "confident", "encouraged", "cared",
    # Hindi (Transliterated & Devanagari)
    "theek", "shant", "behtar", "acha", "accha", "khush", "sukoon", "shanti", "himmat", "surakshit",
    "madad", "dhanyawad", "shukriya", "achha", "राहत", "खुश", "शांत", "सुकून", "बेहतर", "अच्छा",
    "सुरक्षित", "हिम्मत", "धन्यवाद", "शुक्रिया", "ठीक", "विश्वास"
}

NEGATIVE_TERMS = {
    # English
    "bad", "terrible", "worst", "hopeless", "sad", "unhappy", "depressed", "afraid", "scared",
    "fear", "threat", "pain", "hurt", "crying", "anxious", "anxiety", "panic", "suicide", "dying",
    "alone", "helpless", "unsafe", "danger", "trauma", "nightmare", "screaming", "beaten", "abused",
    "stress", "stressed", "suffering", "kill", "harm", "distress", "crying", "agony", "shivering",
    # Hindi (Transliterated & Devanagari)
    "dard", "takleef", "dar", "khauf", "chinta", "pareshaan", "pareshan", "akela", "khatra", "marna",
    "gham", "rona", "udaas", "udas", "bebas", "mar", "mara", "darr", "तनाव", "डर", "तकलीफ", "दर्द",
    "परेशान", "अकेला", "खतरा", "रो", "उदास", "बेबस", "चिंता", "यातना", "चीख", "नुकसान", "मारना"
}

EMOTION_KEYWORDS = {
    "distress": [
        "distress", "helpless", "overwhelmed", "suffering", "crying", "trauma", "nightmare", "bebas",
        "pareshan", "takleef", "दर्द", "तकलीफ", "परेशान", "बेबस", "असह्य", "यातना"
    ],
    "fear": [
        "fear", "scared", "afraid", "threat", "threatened", "danger", "unsafe", "attack", "terror",
        "dar", "darr", "khauf", "khatra", "डर", "खतरा", "खौफ", "भय", "हमला"
    ],
    "sadness": [
        "sad", "depressed", "hopeless", "grief", "lonely", "alone", "crying", "tears", "loss",
        "udas", "udaas", "rona", "akela", "dukhi", "उदास", "रोना", "अकेला", "दुखी", "मायूसी"
    ],
    "anxiety": [
        "anxious", "anxiety", "panic", "worried", "nervous", "shaking", "restless", "palpitations",
        "chinta", "ghabrahat", "bechaini", "चिंता", "घबराहट", "बेचैनी", "तनाव"
    ],
    "anger": [
        "angry", "mad", "furious", "rage", "hatred", "revenge", "unfair", "cheated", "betrayed",
        "gussa", "krodh", "dhokha", "गुस्सा", "क्रोध", "धोखा", "नफरत"
    ],
    "hope": [
        "hope", "better", "healing", "trying", "looking forward", "faith", "believe", "pray",
        "himmat", "umeed", "aasra", "behtar", "उम्मीद", "हिम्मत", "विश्वास", "सुधार", "प्रार्थना"
    ],
    "calm": [
        "calm", "safe", "relieved", "peaceful", "quiet", "rested", "comfortable", "breathe",
        "shant", "sukoon", "theek", "shanti", "शांत", "सुकून", "शांति", "आराम", "राहत"
    ],
}


class TextAnalyzer:
    """Multilingual text analysis for sentiment and emotion detection (Ultra-Lightweight)."""

    def __init__(self) -> None:
        self._loaded = True

    def load_models(self) -> None:
        """Fast initialization requiring zero heavy downloads."""
        self._loaded = True
        logger.info("Ultra-lightweight text analyzer initialized successfully (Memory footprint < 1MB)")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Calculates sentiment polarity (positive, negative, neutral)
        using lexical and semantic valence markers.
        """
        lower_text = text.lower()
        words = re.findall(r'\b\w+\b', lower_text)

        pos_count = sum(1 for w in words if w in POSITIVE_TERMS)
        neg_count = sum(1 for w in words if w in NEGATIVE_TERMS)

        # Check for phrase matches
        for term in POSITIVE_TERMS:
            if " " in term and term in lower_text:
                pos_count += 2
        for term in NEGATIVE_TERMS:
            if " " in term and term in lower_text:
                neg_count += 2

        total = pos_count + neg_count
        if total == 0:
            label = "neutral"
            confidence = 0.65
            scores = [
                {"label": "neutral", "score": 0.65},
                {"label": "negative", "score": 0.20},
                {"label": "positive", "score": 0.15},
            ]
        elif neg_count > pos_count:
            label = "negative"
            confidence = min(0.98, max(0.55, 0.50 + (neg_count / (total + 1)) * 0.45))
            scores = [
                {"label": "negative", "score": round(confidence, 4)},
                {"label": "neutral", "score": round((1.0 - confidence) * 0.7, 4)},
                {"label": "positive", "score": round((1.0 - confidence) * 0.3, 4)},
            ]
        elif pos_count > neg_count:
            label = "positive"
            confidence = min(0.98, max(0.55, 0.50 + (pos_count / (total + 1)) * 0.45))
            scores = [
                {"label": "positive", "score": round(confidence, 4)},
                {"label": "neutral", "score": round((1.0 - confidence) * 0.7, 4)},
                {"label": "negative", "score": round((1.0 - confidence) * 0.3, 4)},
            ]
        else:
            label = "neutral"
            confidence = 0.50
            scores = [
                {"label": "neutral", "score": 0.50},
                {"label": "negative", "score": 0.25},
                {"label": "positive", "score": 0.25},
            ]

        return {
            "label": label,
            "confidence": round(confidence, 4),
            "all_scores": scores,
        }

    def analyze_emotions(self, text: str) -> List[Dict]:
        """
        Classifies emotions across candidate labels defined in config.EMOTION_LABELS:
        (fear, sadness, anger, calm, distress, anxiety, hope, neutral)
        """
        lower_text = text.lower()
        emotion_scores: Dict[str, float] = {label: 0.05 for label in EMOTION_LABELS}

        for emo, keywords in EMOTION_KEYWORDS.items():
            if emo in emotion_scores:
                for kw in keywords:
                    if kw in lower_text:
                        emotion_scores[emo] += 0.35

        # Normalize scores so they sum cleanly
        total = sum(emotion_scores.values())
        if total > 0:
            for emo in emotion_scores:
                emotion_scores[emo] = round(emotion_scores[emo] / total, 4)

        results = [{"label": emo, "score": score} for emo, score in emotion_scores.items()]
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def analyze(self, text: str, language: str = "en") -> Dict:
        """Full text analysis: sentiment + emotion."""
        sentiment = self.analyze_sentiment(text)
        emotions = self.analyze_emotions(text)

        return {
            "sentiment": {
                "label": sentiment["label"],
                "confidence": sentiment["confidence"],
            },
            "emotions": emotions,
            "language": language,
            "text_length": len(text),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
text_analyzer = TextAnalyzer()
