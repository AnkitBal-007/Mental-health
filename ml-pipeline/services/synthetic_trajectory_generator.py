"""
Synthetic Longitudinal Trajectory Generator.

Generates realistic time-series trajectories of distress scores to train
the escalation-prediction model.

PROVENANCE:
- All data generated is 100% synthetic.
- Complies with SIH project rule: "Never use real victim data, even for testing.
  Synthetic data only."

Patterns generated:
  1. Gradual Decline (rising distress): Distress score creeping up over time
     due to prolonged trial delays, economic strain, or social isolation.
  2. Sudden Trigger Spike: Relatively stable baseline followed by an abrupt jump
     due to court hearings, witness threats, or intimidation.
  3. Stable Low-Risk: Resilient recovery or low trauma impact, score stays in 10-35.
  4. Recovering Trend: High initial distress (60-90) steadily decreasing (20-35)
     as rehabilitation, compensation, or counselling takes effect.
  5. High-Risk Volatile: High average distress with erratic oscillations.
"""

import random
from typing import List, Tuple
import numpy as np


def generate_single_trajectory(pattern_type: str, n_points: int = 10) -> Tuple[List[float], int]:
    """
    Generate a single synthetic distress score sequence and its next-step escalation label.

    Returns:
        (history_scores, label) where label=1 means significant escalation occurs
        in the immediate next window, and 0 means no escalation / stable / improving.
    """
    scores = []
    
    if pattern_type == "gradual_decline":
        # Distress is climbing (worsening psychological state)
        start = random.uniform(25, 45)
        slope = random.uniform(2.5, 6.0)
        noise = random.gauss(0, 2.5)
        for i in range(n_points):
            val = start + (i * slope) + random.gauss(0, 2.0)
            scores.append(max(5.0, min(95.0, val)))
        # Next step will escalate further or cross high-risk threshold
        next_val = scores[-1] + slope + random.gauss(0, 2.0)
        label = 1 if (next_val - scores[-1] >= 4.0 or next_val >= 65.0) else 0

    elif pattern_type == "sudden_trigger":
        # Stable baseline, then an abrupt threat or court event causes spike
        baseline = random.uniform(20, 40)
        trigger_idx = random.randint(n_points // 2, n_points - 1)
        for i in range(n_points):
            if i < trigger_idx:
                val = baseline + random.gauss(0, 3.0)
            else:
                # Trigger happens!
                spike = random.uniform(25, 40)
                val = baseline + spike + random.gauss(0, 4.0)
            scores.append(max(5.0, min(98.0, val)))
        # If trigger just happened or is imminent
        if trigger_idx == n_points - 1:
            label = 1
        elif trigger_idx < n_points - 1 and scores[-1] >= 60:
            label = 1
        else:
            label = 0

    elif pattern_type == "stable_low_risk":
        # Low distress fluctuating mildly
        baseline = random.uniform(15, 30)
        for _ in range(n_points):
            val = baseline + random.gauss(0, 3.0)
            scores.append(max(0.0, min(40.0, val)))
        label = 0

    elif pattern_type == "recovering":
        # Initial high distress dropping down steadily
        start = random.uniform(70, 90)
        decay = random.uniform(3.5, 7.0)
        for i in range(n_points):
            val = start - (i * decay) + random.gauss(0, 3.0)
            scores.append(max(10.0, min(95.0, val)))
        label = 0  # Recovering victims do not escalate

    elif pattern_type == "high_risk_volatile":
        # High distress baseline with large swings
        baseline = random.uniform(65, 80)
        for _ in range(n_points):
            val = baseline + random.gauss(0, 8.0)
            scores.append(max(40.0, min(99.0, val)))
        # Volatile high-distress is high risk of crisis escalation
        label = 1 if scores[-1] >= 65 else 0

    else:
        # Default random walk
        curr = random.uniform(30, 60)
        for _ in range(n_points):
            curr = max(5.0, min(95.0, curr + random.gauss(0, 4.0)))
            scores.append(curr)
        label = 1 if scores[-1] >= 65 else 0

    return scores, label


def extract_features_from_scores(scores: List[float], interval_days: float = 3.5) -> np.ndarray:
    """
    Extract fixed-size feature vector from a variable-length score time series.

    Features (10 total):
      0: latest_score           - Current distress score
      1: score_mean             - Average distress over the sequence
      2: score_std              - Volatility / standard deviation
      3: score_velocity         - Linear trend slope per observation
      4: recent_delta           - Change between last two check-ins (latest - prev)
      5: max_score              - Peak distress score seen
      6: min_score              - Minimum distress score seen
      7: acceleration           - Rate of acceleration (recent delta - previous delta)
      8: high_distress_ratio    - Fraction of check-ins with score >= 60
      9: sequence_length        - Number of historical points available
    """
    if not scores:
        return np.zeros(10)

    n = len(scores)
    arr = np.array(scores, dtype=float)

    latest = arr[-1]
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr)) if n > 1 else 0.0
    max_val = float(np.max(arr))
    min_val = float(np.min(arr))

    # Slope / velocity
    if n >= 2:
        x = np.arange(n)
        slope, _ = np.polyfit(x, arr, 1)
        recent_delta = float(arr[-1] - arr[-2])
    else:
        slope = 0.0
        recent_delta = 0.0

    # Acceleration
    if n >= 3:
        prev_delta = float(arr[-2] - arr[-3])
        acceleration = recent_delta - prev_delta
    else:
        acceleration = 0.0

    high_distress_ratio = float(np.mean(arr >= 60.0))

    return np.array([
        latest,
        mean_val,
        std_val,
        float(slope),
        recent_delta,
        max_val,
        min_val,
        acceleration,
        high_distress_ratio,
        float(n)
    ], dtype=float)


FEATURE_NAMES = [
    "Latest Distress Score",
    "Historical Mean Score",
    "Score Volatility (Std Dev)",
    "Distress Velocity (Slope)",
    "Recent Change (Latest - Prev)",
    "Peak Distress Score",
    "Minimum Distress Score",
    "Trend Acceleration",
    "Ratio of High Distress Check-ins",
    "Data Points Count"
]


def generate_synthetic_dataset(n_samples: int = 3000, random_seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic dataset for training the escalation classifier.

    Returns:
        (X, y): Feature matrix (n_samples, 10) and binary targets (n_samples,).
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    patterns = [
        ("gradual_decline", 0.30),
        ("sudden_trigger", 0.25),
        ("stable_low_risk", 0.20),
        ("recovering", 0.15),
        ("high_risk_volatile", 0.10)
    ]

    X_list = []
    y_list = []

    for pattern_type, weight in patterns:
        count = int(n_samples * weight)
        for _ in range(count):
            seq_len = random.randint(3, 14)
            scores, label = generate_single_trajectory(pattern_type, n_points=seq_len)
            features = extract_features_from_scores(scores)
            X_list.append(features)
            y_list.append(label)

    X = np.array(X_list)
    y = np.array(y_list)

    return X, y
