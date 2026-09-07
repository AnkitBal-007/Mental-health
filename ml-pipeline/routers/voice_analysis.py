"""Router for POST /analyze/voice."""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from schemas.voice import VoiceAnalysisResponse
from services.voice_analyzer import voice_analyzer

router = APIRouter(prefix="/analyze", tags=["Voice Analysis"])

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".webm"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("/voice", response_model=VoiceAnalysisResponse)
async def analyze_voice(
    file: UploadFile = File(..., description="Audio file to analyze"),
):
    """
    Analyze a voice recording for transcription and stress features.

    Accepts audio files (WAV, MP3, OGG, FLAC, M4A, WebM — max 25 MB).
    Returns the Whisper transcript, prosodic features (pitch, speaking
    rate, pause ratio, energy), and rule-based stress indicators.
    """
    if not voice_analyzer.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Voice analysis models are still loading. Try again shortly.",
        )

    # Validate file type
    ext = Path(file.filename or "audio.wav").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported audio format '{ext}'. "
                f"Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    # Read and validate size
    audio_bytes = await file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, detail="File too large (max 25 MB)"
        )

    try:
        result = await voice_analyzer.analyze(
            audio_bytes, file.filename or "audio.wav"
        )
        return VoiceAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Voice analysis failed: {e}"
        )
