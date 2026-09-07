"""
Intervention Recommendation Engine.

Dynamically loads rules from an external JSON configuration file (config/recommendation_rules.json)
and evaluates:
  1. Victim's Dynamic Distress Score (0–100)
  2. Contributing psychological and situational factors (from ML pipeline /explain/distress)
  3. Legal case type (e.g. rape, murder_witness, caste_based_violence, atrocity_act, intimidation)

Returns a transparently ranked list of suggested interventions:
  - counselling
  - medical (medical referral & psychiatric evaluation)
  - protection (witness protection & security escort)
  - relocation (safe house / shelter support)
  - financial (interim victim relief disbursement)
  - legal_aid (DLSA legal representation & trial notifications)

COMPLIANCE & TRANSPARENCY:
- "Keep the mapping transparent and editable — store it as a JSON config file, not hardcoded in Python."
- "No feature may auto-execute an intervention. The system recommends; a human decides and confirms."
"""

import json
import logging
import os
from typing import List, Dict, Optional, Tuple

from config import RECOMMENDATION_RULES_PATH
from schemas.recommendation import InterventionItem

logger = logging.getLogger(__name__)


def load_recommendation_rules() -> List[Dict]:
    """
    Load recommendation rules from the JSON configuration file.
    Reads dynamically from disk so adjustments during demos or judge Q&A take effect immediately.
    """
    if not os.path.exists(RECOMMENDATION_RULES_PATH):
        logger.warning("Rules file not found at %s. Using default fallback rules.", RECOMMENDATION_RULES_PATH)
        return []

    try:
        with open(RECOMMENDATION_RULES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("rules", [])
    except Exception as e:
        logger.error("Error reading recommendation rules from %s: %s", RECOMMENDATION_RULES_PATH, e)
        return []


def normalize_case_type(case_type: str) -> str:
    """Normalize aliases for case types."""
    c = case_type.lower().strip()
    synonyms = {
        "rape": "rape",
        "sexual_violence": "sexual_violence",
        "gang_rape": "gang_rape",
        "murder_witness": "murder_witness",
        "murder_threat": "murder_threat",
        "intimidation": "intimidation",
        "caste_based_violence": "caste_based_violence",
        "atrocity_act": "atrocity_act",
        "grievous_hurt": "grievous_hurt",
        "arson": "arson",
    }
    return synonyms.get(c, c)


def evaluate_recommendations(
    case_type: str,
    distress_score: float,
    contributing_factors: Optional[List[str]] = None,
    escalation_prob: Optional[float] = 0.0,
) -> List[InterventionItem]:
    """
    Evaluate candidate intervention rules and return a ranked list of interventions.

    Args:
        case_type: Victim case category (e.g. 'rape', 'murder_witness', 'caste_based_violence', 'intimidation')
        distress_score: Dynamic Distress Score (0-100)
        contributing_factors: List of factor names/descriptions from explainability engine
        escalation_prob: Escalation probability (0-1)

    Returns:
        List of InterventionItem objects sorted by priority and computed ranking score (highest first).
    """
    rules = load_recommendation_rules()
    factors_list = [f.lower() for f in (contributing_factors or [])]
    factors_text = " ".join(factors_list)
    norm_case = normalize_case_type(case_type)

    matched_interventions: List[Tuple[float, InterventionItem]] = []

    for rule in rules:
        min_score = float(rule.get("min_distress_score", 0.0))
        applicable_cases = [c.lower() for c in rule.get("applicable_case_types", ["*"])]
        trigger_factors = [tf.lower() for tf in rule.get("trigger_factors", ["*"])]
        base_weight = float(rule.get("base_score", 50.0))

        # 1. Check distress score threshold
        score_matched = distress_score >= min_score

        # 2. Check case type match
        case_matched = (
            "*" in applicable_cases or 
            "all" in applicable_cases or 
            norm_case in applicable_cases or
            any(ac in norm_case for ac in applicable_cases if ac != "*")
        )

        # 3. Check factor keyword match
        matched_trigger_keywords = []
        if "*" in trigger_factors or "all" in trigger_factors:
            factor_matched = True
        else:
            for tf in trigger_factors:
                if tf in factors_text or any(tf in f for f in factors_list):
                    matched_trigger_keywords.append(tf)
            factor_matched = len(matched_trigger_keywords) > 0 or not factors_list

        # Rule triggers if case type matches and distress score threshold is met
        if case_matched and score_matched:
            # Compute dynamic ranking score
            ranking_score = base_weight
            ranking_score += (distress_score * 0.25)
            if escalation_prob and escalation_prob >= 0.6:
                ranking_score += 10.0
            if matched_trigger_keywords:
                ranking_score += (len(matched_trigger_keywords) * 4.0)

            # Build transparent justification
            reasons = []
            reasons.append(f"Distress score ({distress_score:.1f} >= {min_score:.0f})")
            if norm_case in applicable_cases:
                reasons.append(f"Matches legal case type '{case_type}'")
            if matched_trigger_keywords:
                reasons.append(f"Triggered by psychological signals: [{', '.join(matched_trigger_keywords)}]")

            justification = f"Priority justification: {'; '.join(reasons)}."

            item = InterventionItem(
                category=rule["category"],
                title=rule["title"],
                description=rule["description"],
                priority=rule["priority"],
                recommended_authority=rule["recommended_authority"],
                ranking_score=round(ranking_score, 1),
                reason=justification,
            )
            matched_interventions.append((ranking_score, item))

    # Sort descending by ranking score (highest urgency first)
    matched_interventions.sort(key=lambda x: x[0], reverse=True)

    # Return deduplicated by category + title (keep highest scored)
    seen_titles = set()
    final_items: List[InterventionItem] = []
    for _, item in matched_interventions:
        if item.title not in seen_titles:
            seen_titles.add(item.title)
            final_items.append(item)

    return final_items


# Backward compatibility alias
def get_recommendations_for_victim(
    case_type: str,
    risk_level: str,
    distress_score: float,
    escalation_prob: float,
    factors: Optional[List[str]] = None,
) -> List[InterventionItem]:
    return evaluate_recommendations(
        case_type=case_type,
        distress_score=distress_score,
        contributing_factors=factors,
        escalation_prob=escalation_prob,
    )

