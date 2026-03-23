import subprocess
import tempfile
import logging
from pathlib import Path

from faster_whisper import WhisperModel

import config

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        logger.info("Loading Whisper model '%s' on %s...", config.WHISPER_MODEL, config.WHISPER_DEVICE)
        _model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
        logger.info("Whisper model loaded.")
    return _model


def extract_audio(video_path: Path) -> Path:
    """Extract audio from video to a temporary WAV file using ffmpeg."""
    audio_path = Path(tempfile.gettempdir()) / f"{video_path.stem}.wav"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(audio_path),
    ]
    logger.info("Extracting audio: %s", video_path.name)
    subprocess.run(cmd, capture_output=True, check=True)
    return audio_path


def transcribe(video_path: Path) -> str:
    """Transcribe a video file and return the full transcript text."""
    audio_path = extract_audio(video_path)
    try:
        model = _get_model()
        logger.info("Transcribing: %s", video_path.name)
        segments, info = model.transcribe(str(audio_path), beam_size=5)
        logger.info("Detected language: %s (prob %.2f)", info.language, info.language_probability)

        lines = []
        for segment in segments:
            lines.append(segment.text.strip())

        transcript = "\n".join(lines)
        logger.info("Transcription complete — %d characters.", len(transcript))
        return transcript
    finally:
        audio_path.unlink(missing_ok=True)
