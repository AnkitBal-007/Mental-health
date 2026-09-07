"""
Distress scoring service.

The scoring formula is isolated in compute_distress_score() so it can be
swapped for a trained model later without changing the API contract.

CURRENT IMPLEMENTATION: weighted rule-based scoring (not ML-trained).
SYNTHETIC DATA ONLY — trained on no real victim data.

Scoring breakdown (max 100 points):
  - Sentiment component:        0–40 pts  (negative sentiment → higher distress)
  - Emotion component:          0–35 pts  (high-distress emotions → higher score)
  - Engagement component:       0–15 pts  (low engagement / missed check-ins)
  - Missed check-in penalty:    0–10 pts  (additional penalty for very low engagement)

All components are weighted by recency (recent check-ins matter more).
"""

import logging
from typing import Dict, List, Tuple

from schemas.distress import InteractionRecord

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Emotion → distress-weight mapping (higher = more distressing)
# ---------------------------------------------------------------------------
EMOTION_DISTRESS_WEIGHTS: Dict[str, float] = {
    "distress": 0.95,
    "fear": 0.85,
    "anxiety": 0.80,
    "sadness": 0.75,
    "anger": 0.65,
    "neutral": 0.30,
    "calm": 0.10,
    "hope": 0.05,
}

DEFAULT_EMOTION_WEIGHT = 0.50


# ---------------------------------------------------------------------------
# Core scoring function — SWAP THIS for a trained model when ready
# ---------------------------------------------------------------------------


def compute_distress_score(interactions: List[InteractionRecord]) -> Dict:
    """
    Compute a Dynamic Distress Score (0-100) from recent interactions.

    This is the function to replace when a trained model (e.g. XGBoost
    on longitudinal data) becomes available.  The API contract stays the
    same: it takes a list of InteractionRecord objects and returns a dict
    with distress_score, factors, confidence, and interactions_analyzed.

    Current approach:
      For each interaction, compute:
        sentiment_component  = (1 − normalized_sentiment) × 40
        emotion_component    = emotion_distress_weight   × 35
        engagement_component = (1 − engagement_score)    × 15

      Apply recency weighting (recent check-ins count more), then add a
      missed-check-in penalty (up to 10 points).

    Args:
        interactions: List of InteractionRecord objects from recent check-ins.

    Returns:
        Dict with keys: distress_score, factors, confidence, interactions_analyzed.
    """
    if not interactions:
        return {
            "distress_score": 0.0,
            "factors": [],
            "confidence": 0.0,
            "interactions_analyzed": 0,
        }

    # Sort oldest → newest
    sorted_interactions = sorted(interactions, key=lambda x: x.timestamp)
    n = len(sorted_interactions)

    # Per-interaction accumulators
    weighted_scores: List[float] = []
    recency_weights: List[float] = []
    sentiment_values: List[float] = []
    emotion_values: List[float] = []
    engagement_values: List[float] = []

    for i, interaction in enumerate(sorted_interactions):
        # Recency: 0→1, most recent = 1.0
        recency = (i + 1) / n
        recency_weight = recency ** 1.5  # gentle exponential emphasis
        recency_weights.append(recency_weight)

        # 1) Sentiment component (0-40 pts)
        norm_sentiment = (interaction.sentiment_score + 1) / 2  # [−1,1] → [0,1]
        sentiment_distress = (1 - norm_sentiment) * 40
        sentiment_values.append(sentiment_distress)

        # 2) Emotion component (0-35 pts)
        emotion_weight = EMOTION_DISTRESS_WEIGHTS.get(
            interaction.emotion_label.lower(), DEFAULT_EMOTION_WEIGHT
        )
        emotion_distress = emotion_weight * 35
        emotion_values.append(emotion_distress)

        # 3) Engagement component (0-15 pts)
        engagement_distress = (1 - interaction.engagement_score) * 15
        engagement_values.append(engagement_distress)

        # Combined
        interaction_score = sentiment_distress + emotion_distress + engagement_distress
        weighted_scores.append(interaction_score * recency_weight)

    # Weighted average
    total_weight = sum(recency_weights)
    base_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0

    # 4) Missed-check-in penalty (0-10 pts)
    low_engagement_count = sum(
        1 for i in sorted_interactions if i.engagement_score < 0.3
    )
    missed_ratio = low_engagement_count / n
    missed_penalty = missed_ratio * 10

    # Final score clamped to [0, 100]
    distress_score = min(100.0, max(0.0, base_score + missed_penalty))

    # ----- Factor breakdown (plain-language, per design guidelines) -----
    avg_sentiment = sum(sentiment_values) / n
    avg_emotion = sum(emotion_values) / n
    avg_engagement = sum(engagement_values) / n

    last = sorted_interactions[-1]
    recent_sentiment_label = (
        "negative"
        if last.sentiment_score < -0.2
        else "positive"
        if last.sentiment_score > 0.2
        else "neutral"
    )

    factors = [
        {
            "factor": "Sentiment pattern",
            "contribution": round(avg_sentiment, 1),
            "detail": (
                f"Recent sentiment is {recent_sentiment_label} "
                f"(latest score: {last.sentiment_score:.2f}), "
                f"contributing ~{avg_sentiment:.0f} points"
            ),
        },
        {
            "factor": "Emotional state",
            "contribution": round(avg_emotion, 1),
            "detail": (
                f"Predominant recent emotion: {last.emotion_label}, "
                f"contributing ~{avg_emotion:.0f} points"
            ),
        },
    ]

    if avg_engagement > 2:
        factors.append(
            {
                "factor": "Engagement decline",
                "contribution": round(avg_engagement, 1),
                "detail": (
                    f"Low engagement detected in recent check-ins, "
                    f"contributing ~{avg_engagement:.0f} points"
                ),
            }
        )

    if missed_penalty > 1:
        factors.append(
            {
                "factor": "Missed/low-engagement check-ins",
                "contribution": round(missed_penalty, 1),
                "detail": (
                    f"{low_engagement_count} of {n} check-ins had very low "
                    f"engagement, adding {missed_penalty:.0f} penalty points"
                ),
            }
        )

    # Sort by contribution descending (largest first — per design spec)
    factors.sort(key=lambda f: f["contribution"], reverse=True)

    # Confidence grows with more data, caps at 1.0 with 10+ interactions
    confidence = min(1.0, n / 10)

    return {
        "distress_score": round(distress_score, 1),
        "factors": factors,
        "confidence": round(confidence, 2),
        "interactions_analyzed": n,
    }


# ---------------------------------------------------------------------------
# Trend computation
# ---------------------------------------------------------------------------


def compute_trend(
    interactions: List[InteractionRecord], window: int = 5
) -> Tuple[str, str]:
    """
    Determine trend direction from the last ``window`` interactions.

    Compares average distress-proxy of the first half vs. second half of
    the window.

    Returns:
        (trend_label, trend_detail) — e.g. ("worsening", "Distress indicators
        increased by 8.3 points over the last 5 check-ins").
    """
    if len(interactions) < 3:
        return (
            "stable",
            "Insufficient data for trend analysis (need at least 3 check-ins)",
        )

    sorted_ints = sorted(interactions, key=lambda x: x.timestamp)
    recent = sorted_ints[-window:] if len(sorted_ints) >= window else sorted_ints

    n = len(recent)
    mid = n // 2

    def _distress_proxy(record: InteractionRecord) -> float:
        """Quick single-record distress estimate for trend comparison."""
        sentiment_part = (1 - (record.sentiment_score + 1) / 2) * 50
        emotion_w = EMOTION_DISTRESS_WEIGHTS.get(
            record.emotion_label.lower(), DEFAULT_EMOTION_WEIGHT
        )
        emotion_part = emotion_w * 30
        engagement_part = (1 - record.engagement_score) * 20
        return sentiment_part + emotion_part + engagement_part

    first_half = [_distress_proxy(r) for r in recent[:mid]]
    second_half = [_distress_proxy(r) for r in recent[mid:]]

    avg_first = sum(first_half) / len(first_half) if first_half else 0
    avg_second = sum(second_half) / len(second_half) if second_half else 0

    diff = avg_second - avg_first
    threshold = 5.0  # Points of change needed to register as a trend

    if diff > threshold:
        return (
            "worsening",
            f"Distress indicators increased by {diff:.1f} points "
            f"over the last {n} check-ins",
        )
    elif diff < -threshold:
        return (
            "improving",
            f"Distress indicators decreased by {abs(diff):.1f} points "
            f"over the last {n} check-ins",
        )
    else:
        return (
            "stable",
            f"Distress indicators remained relatively stable "
            f"(change: {abs(diff):.1f} points) over the last {n} check-ins",
        )


# ---------------------------------------------------------------------------
# Explainability — detailed factor breakdown for /explain/distress
# ---------------------------------------------------------------------------


def explain_distress_score(interactions: List[InteractionRecord]) -> Dict:
    """
    Produce a granular, human-readable explanation of the distress score.

    This function computes the same score as compute_distress_score() but
    decomposes it into fine-grained factors that sum approximately to the
    total score.  Each factor has:
      - factor:       short label (e.g. "Declining sentiment trend")
      - contribution: point contribution (e.g. 18.0)
      - description:  plain-language explanation for non-technical reviewers

    SCORING METHOD: rule-based (transparent weighted breakdown).
    When a trained model (XGBoost / scikit-learn) is used instead, replace
    this function body with SHAP-based explanations:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(features)
        # map shap_values to factor dicts

    Returns:
        Dict with keys: distress_score, factors, scoring_method, confidence,
        interactions_analyzed, trend, trend_detail.
    """
    if not interactions:
        return {
            "distress_score": 0.0,
            "factors": [],
            "scoring_method": "rule-based",
            "confidence": 0.0,
            "interactions_analyzed": 0,
        }

    sorted_ints = sorted(interactions, key=lambda x: x.timestamp)
    n = len(sorted_ints)
    factors: List[Dict] = []

    # === 1. Current sentiment level (0–20 pts) ===
    # How negative is the recent sentiment (last 3 or fewer check-ins)?
    recent_window = sorted_ints[-min(3, n) :]
    avg_recent_sentiment = sum(r.sentiment_score for r in recent_window) / len(
        recent_window
    )
    # Map [-1, 1] → [0, 1] inverted, then scale to 20
    sentiment_level_pts = (1 - (avg_recent_sentiment + 1) / 2) * 20

    sentiment_label = (
        "very negative"
        if avg_recent_sentiment < -0.5
        else "negative"
        if avg_recent_sentiment < -0.2
        else "neutral"
        if avg_recent_sentiment <= 0.2
        else "positive"
    )
    factors.append(
        {
            "factor": "Current sentiment level",
            "contribution": round(sentiment_level_pts, 1),
            "description": (
                f"Average recent sentiment is {sentiment_label} "
                f"(score: {avg_recent_sentiment:+.2f}): "
                f"+{sentiment_level_pts:.0f} points"
            ),
        }
    )

    # === 2. Declining sentiment trend (0–18 pts) ===
    if n >= 3:
        mid = n // 2
        avg_first_half = sum(r.sentiment_score for r in sorted_ints[:mid]) / mid
        avg_second_half = sum(
            r.sentiment_score for r in sorted_ints[mid:]
        ) / len(sorted_ints[mid:])
        # Positive decline = sentiment got worse (first half higher than second)
        decline = avg_first_half - avg_second_half
        trend_pts = max(0.0, decline * 18)  # scale: full -1→+1 swing = 18 pts
    else:
        decline = 0.0
        trend_pts = 0.0

    if trend_pts > 0.5:
        factors.append(
            {
                "factor": "Declining sentiment trend",
                "contribution": round(trend_pts, 1),
                "description": (
                    f"Sentiment declined by {decline:+.2f} (from "
                    f"{avg_first_half:+.2f} avg to {avg_second_half:+.2f} avg) "
                    f"across {n} check-ins: +{trend_pts:.0f} points"
                ),
            }
        )

    # === 3. Negative emotion predominance (0–20 pts) ===
    distressing_emotions = {"distress", "fear", "anxiety", "sadness", "anger"}
    distressing_count = sum(
        1
        for r in sorted_ints
        if r.emotion_label.lower() in distressing_emotions
    )
    emotion_ratio = distressing_count / n
    emotion_pts = emotion_ratio * 20

    dominant_emotions = {}
    for r in sorted_ints:
        lbl = r.emotion_label.lower()
        dominant_emotions[lbl] = dominant_emotions.get(lbl, 0) + 1
    top_emotion = max(dominant_emotions, key=dominant_emotions.get)

    factors.append(
        {
            "factor": "Negative emotion predominance",
            "contribution": round(emotion_pts, 1),
            "description": (
                f"{distressing_count} of {n} check-ins showed distressing "
                f"emotions (most common: {top_emotion}): "
                f"+{emotion_pts:.0f} points"
            ),
        }
    )

    # === 4. High emotional volatility (0–12 pts) ===
    emotion_sequence = [r.emotion_label.lower() for r in sorted_ints]
    switches = sum(
        1
        for i in range(1, len(emotion_sequence))
        if emotion_sequence[i] != emotion_sequence[i - 1]
    )
    volatility_ratio = switches / max(1, n - 1) if n > 1 else 0
    # Only contributes if volatility > 30% (some switching is normal)
    volatility_pts = max(0.0, (volatility_ratio - 0.3) * 12 / 0.7)

    if volatility_pts > 0.5:
        unique_count = len(set(emotion_sequence))
        factors.append(
            {
                "factor": "High emotional volatility",
                "contribution": round(volatility_pts, 1),
                "description": (
                    f"Emotions shifted {switches} times across {unique_count} "
                    f"different states in {n} check-ins "
                    f"(volatility: {volatility_ratio:.0%}): "
                    f"+{volatility_pts:.0f} points"
                ),
            }
        )

    # === 5. Latest check-in severity (0–15 pts) ===
    latest = sorted_ints[-1]
    latest_emotion_w = EMOTION_DISTRESS_WEIGHTS.get(
        latest.emotion_label.lower(), DEFAULT_EMOTION_WEIGHT
    )
    latest_sentiment_component = (1 - (latest.sentiment_score + 1) / 2) * 8
    latest_emotion_component = latest_emotion_w * 7
    latest_pts = latest_sentiment_component + latest_emotion_component

    factors.append(
        {
            "factor": "Latest check-in severity",
            "contribution": round(latest_pts, 1),
            "description": (
                f"Most recent check-in: sentiment {latest.sentiment_score:+.2f}, "
                f"emotion '{latest.emotion_label}' "
                f"(weight {latest_emotion_w:.2f}): +{latest_pts:.0f} points"
            ),
        }
    )

    # === 6. Missed / low-engagement check-ins (0–12 pts) ===
    low_engagement_count = sum(
        1 for r in sorted_ints if r.engagement_score < 0.3
    )
    missed_pts = (low_engagement_count / n) * 12

    if missed_pts > 0.5:
        factors.append(
            {
                "factor": f"Missed last {low_engagement_count} check-in"
                + ("s" if low_engagement_count != 1 else ""),
                "contribution": round(missed_pts, 1),
                "description": (
                    f"{low_engagement_count} of {n} check-ins had very low "
                    f"engagement (< 0.3), suggesting missed or abandoned "
                    f"interactions: +{missed_pts:.0f} points"
                ),
            }
        )

    # === 7. Engagement decline trend (0–8 pts) ===
    if n >= 3:
        mid = n // 2
        eng_first = sum(r.engagement_score for r in sorted_ints[:mid]) / mid
        eng_second = sum(
            r.engagement_score for r in sorted_ints[mid:]
        ) / len(sorted_ints[mid:])
        eng_decline = eng_first - eng_second  # positive = engagement dropped
        eng_pts = max(0.0, eng_decline * 8)
    else:
        eng_decline = 0.0
        eng_pts = 0.0

    if eng_pts > 0.5:
        factors.append(
            {
                "factor": "Engagement decline",
                "contribution": round(eng_pts, 1),
                "description": (
                    f"Engagement dropped from {eng_first:.2f} avg to "
                    f"{eng_second:.2f} avg over {n} check-ins: "
                    f"+{eng_pts:.0f} points"
                ),
            }
        )

    # ----- Compute raw total and normalize to match actual distress score -----
    score_result = compute_distress_score(interactions)
    actual_score = score_result["distress_score"]

    raw_total = sum(f["contribution"] for f in factors)
    if raw_total > 0 and actual_score > 0:
        scale = actual_score / raw_total
        for f in factors:
            f["contribution"] = round(f["contribution"] * scale, 1)
    # Re-round descriptions after scaling
    for f in factors:
        f["description"] = f["description"].rsplit("+", 1)[0] + (
            f"+{f['contribution']:.0f} points"
        )

    # Sort by contribution descending (largest first — per design spec)
    factors.sort(key=lambda f: f["contribution"], reverse=True)

    # Trend
    trend_label, trend_detail = compute_trend(interactions)

    # Confidence
    confidence = min(1.0, n / 10)

    return {
        "distress_score": actual_score,
        "factors": factors,
        "scoring_method": "rule-based",
        "confidence": round(confidence, 2),
        "interactions_analyzed": n,
        "trend": trend_label,
        "trend_detail": trend_detail,
    }

