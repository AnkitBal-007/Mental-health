"""
Text analysis service — multilingual sentiment + emotion classification.

Sentiment model:  cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual
                  (supports Hindi, English, and 6 other languages)
Emotion model:    MoritzLaurer/mDeBERTa-v3-base-mnli-xnli
                  (zero-shot classification with multilingual NLI)

Both are rule-based in the sense that the pipeline is fixed; the underlying
models are pre-trained transformers.  Document this in the module README per
project rules.
"""

import logging
from typing import Dict, List

from transformers import pipeline

from config import EMOTION_LABELS, EMOTION_MODEL, SENTIMENT_MODEL

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """Multilingual text analysis for sentiment and emotion detection."""

    def __init__(self) -> None:
        self._sentiment_pipeline = None
        self._emotion_pipeline = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def load_models(self) -> None:
        """Load ML models.  Call once at startup (via FastAPI lifespan)."""
        logger.info("Loading sentiment model: %s", SENTIMENT_MODEL)
        self._sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=SENTIMENT_MODEL,
            top_k=None,
            device=-1,  # CPU — change to 0 for GPU
        )

        logger.info("Loading emotion model: %s", EMOTION_MODEL)
        self._emotion_pipeline = pipeline(
            "zero-shot-classification",
            model=EMOTION_MODEL,
            device=-1,
        )

        self._loaded = True
        logger.info("Text analysis models loaded successfully")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Analysis methods
    # ------------------------------------------------------------------

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Return the top sentiment label with confidence, plus all scores.

        The XLM-RoBERTa model returns labels: positive / neutral / negative.
        """
        results = self._sentiment_pipeline(text)
        # pipeline(top_k=None) returns [[{label, score}, ...]]
        scores = results[0] if isinstance(results[0], list) else results

        # Normalize label casing
        label_map = {
            "positive": "positive",
            "negative": "negative",
            "neutral": "neutral",
            "Positive": "positive",
            "Negative": "negative",
            "Neutral": "neutral",
        }

        formatted = []
        for item in scores:
            label = label_map.get(item["label"], item["label"].lower())
            formatted.append({"label": label, "score": round(item["score"], 4)})

        formatted.sort(key=lambda x: x["score"], reverse=True)
        top = formatted[0]

        return {
            "label": top["label"],
            "confidence": top["score"],
            "all_scores": formatted,
        }

    def analyze_emotions(self, text: str) -> List[Dict]:
        """
        Classify emotions via zero-shot NLI.

        Candidate labels are defined in config.EMOTION_LABELS (fear, sadness,
        anger, calm, distress, anxiety, hope, neutral).
        """
        result = self._emotion_pipeline(
            text,
            candidate_labels=EMOTION_LABELS,
            multi_label=False,
        )

        emotions = []
        for label, score in zip(result["labels"], result["scores"]):
            emotions.append({"label": label, "score": round(score, 4)})

        return emotions

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, text: str, language: str = "en") -> Dict:
        """
        Full text analysis: sentiment + emotion.

        Returns a dict matching TextAnalysisResponse schema.
        """
        if not self._loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")

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
# Module-level singleton — imported by the router
# ---------------------------------------------------------------------------
text_analyzer = TextAnalyzer()
