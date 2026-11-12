import logging
import wave
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def diarize(audio_path: Path) -> list[tuple[float, float, str]]:
    """Return speaker turns as (start_seconds, end_seconds, label), in time order.

    torch and pyannote are imported here so the rest of the pipeline works
    without them installed.
    """
    import numpy as np
    import torch
    from pyannote.audio import Pipeline

    logger.info("Loading diarization model '%s'...", config.DIARIZATION_MODEL)
    pipeline = Pipeline.from_pretrained(config.DIARIZATION_MODEL)
    if torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))

    # Feed the waveform in memory: pyannote's own file decoding goes through
    # torchcodec, which needs FFmpeg shared libraries that Windows lacks.
    with wave.open(str(audio_path), "rb") as wav:
        sample_rate = wav.getframerate()
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
    waveform = torch.from_numpy(pcm.astype(np.float32) / 32768.0).unsqueeze(0)

    logger.info("Identifying speakers: %.1f minutes of audio", len(pcm) / sample_rate / 60)
    output = pipeline({"waveform": waveform, "sample_rate": sample_rate})

    # The exclusive variant has no overlapping turns, so every word maps to one speaker.
    turns = [
        (segment.start, segment.end, label)
        for segment, _, label in output.exclusive_speaker_diarization.itertracks(yield_label=True)
    ]
    logger.info("Found %d speaker(s).", len({label for _, _, label in turns}))
    return turns
