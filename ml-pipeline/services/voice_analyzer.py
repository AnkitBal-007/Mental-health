"""
Voice analysis service — Whisper transcription + librosa prosodic features.

Components:
  - Transcription:  OpenAI Whisper (configurable size via WHISPER_MODEL_SIZE)
  - Prosodic features (librosa):
      • Pitch (F0) mean and variance  — via pyin
      • Speaking rate                  — onset-detection-based estimate
      • Pause ratio                    — silent vs. voiced duration
      • Energy (RMS) mean and variance
  - Stress indicators:  rule-based flags derived from prosodic features.
    Thresholds are approximate and documented inline; in production these
    would be calibrated per-speaker or learned from data.

Requires ffmpeg on the system PATH for Whisper.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict

import librosa
import numpy as np
import whisper

from config import WHISPER_MODEL_SIZE

logger = logging.getLogger(__name__)


class VoiceAnalyzer:
    """Audio analysis: transcription + prosodic stress features."""

    def __init__(self) -> None:
        self._whisper_model = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def load_models(self) -> None:
        """Load Whisper model.  Call once at startup."""
        logger.info("Loading Whisper model (size=%s)", WHISPER_MODEL_SIZE)
        self._whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
        self._loaded = True
        logger.info("Whisper model loaded successfully")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    def transcribe(self, audio_path: str) -> Dict:
        """Transcribe audio and return text + detected language."""
        result = self._whisper_model.transcribe(audio_path)
        return {
            "transcript": result["text"].strip(),
            "language_detected": result.get("language", "unknown"),
        }

    # ------------------------------------------------------------------
    # Prosodic feature extraction
    # ------------------------------------------------------------------

    def extract_prosodic_features(self, audio_path: str) -> Dict:
        """Extract stress-relevant prosodic features from an audio file."""
        y, sr = librosa.load(audio_path, sr=22050)
        duration = librosa.get_duration(y=y, sr=sr)

        # --- Pitch (F0) via pyin ---
        f0, voiced_flag, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7")
        )
        f0_voiced = (
            f0[voiced_flag] if voiced_flag is not None else f0[~np.isnan(f0)]
        )
        if len(f0_voiced) == 0:
            f0_voiced = np.array([0.0])

        pitch_mean = float(np.mean(f0_voiced))
        pitch_variance = float(np.var(f0_voiced))

        # --- Speaking rate (onset-based syllable estimate) ---
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onsets = librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr, units="time"
        )
        speaking_rate = len(onsets) / duration if duration > 0 else 0.0

        # --- Pause ratio ---
        intervals = librosa.effects.split(y, top_db=30)
        voiced_duration = sum((end - start) for start, end in intervals) / sr
        pause_ratio = 1.0 - (voiced_duration / duration) if duration > 0 else 0.0
        pause_ratio = max(0.0, min(1.0, pause_ratio))

        # --- Energy (RMS) ---
        rms = librosa.feature.rms(y=y)[0]
        energy_mean = float(np.mean(rms))
        energy_variance = float(np.var(rms))

        return {
            "pitch_mean_hz": round(pitch_mean, 2),
            "pitch_variance": round(pitch_variance, 2),
            "speaking_rate_syllables_per_sec": round(speaking_rate, 2),
            "pause_ratio": round(pause_ratio, 4),
            "energy_mean": round(energy_mean, 6),
            "energy_variance": round(energy_variance, 8),
            "duration_seconds": round(duration, 2),
        }

    # ------------------------------------------------------------------
    # Stress indicators (rule-based)
    # ------------------------------------------------------------------

    def compute_stress_indicators(self, features: Dict) -> Dict:
        """
        Derive rule-based stress flags from prosodic features.

        Thresholds are approximate, based on speech-analysis literature:
          • Pitch variance > 2000 Hz² → elevated
          • Speaking rate < 2.0 or > 6.0 syll/s → abnormal
          • Pause ratio > 0.4 → high
          • Energy variance > 0.01 → irregular
        """
        pitch_elevated = features["pitch_variance"] > 2000
        speech_rate_abnormal = (
            features["speaking_rate_syllables_per_sec"] < 2.0
            or features["speaking_rate_syllables_per_sec"] > 6.0
        )
        high_pause = features["pause_ratio"] > 0.4
        energy_irregular = features["energy_variance"] > 0.01

        stress_signals = sum(
            [pitch_elevated, speech_rate_abnormal, high_pause, energy_irregular]
        )

        if stress_signals >= 3:
            level = "high"
        elif stress_signals >= 1:
            level = "moderate"
        else:
            level = "low"

        return {
            "pitch_elevated": pitch_elevated,
            "speech_rate_abnormal": speech_rate_abnormal,
            "high_pause_ratio": high_pause,
            "energy_irregular": energy_irregular,
            "overall_stress_level": level,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(self, audio_bytes: bytes, filename: str = "audio.wav") -> Dict:
        """
        Full voice analysis: transcription + prosodic features + stress indicators.

        Writes audio to a temp file (required by librosa and Whisper),
        cleans up afterwards.
        """
        if not self._loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")

        suffix = Path(filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            transcription = self.transcribe(tmp_path)
            features = self.extract_prosodic_features(tmp_path)
            stress = self.compute_stress_indicators(features)

            return {
                "transcript": transcription["transcript"],
                "language_detected": transcription["language_detected"],
                "duration_seconds": features.pop("duration_seconds"),
                "prosodic_features": features,
                "stress_indicators": stress,
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
voice_analyzer = VoiceAnalyzer()
