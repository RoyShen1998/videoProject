import bisect
import subprocess
import sys
import tempfile
import logging
from pathlib import Path

import config

logger = logging.getLogger(__name__)

# One Whisper segment: its text plus (start_seconds, end_seconds, word) for each
# word. The word list is empty when speaker labelling is off.
Segment = tuple[str, list[tuple[float, float, str]]]


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


def _run_whisper(audio_path: Path, name: str) -> list[Segment]:
    # Imported here so only the child process pays for loading the library.
    from faster_whisper import WhisperModel

    logger.info("Loading Whisper model '%s' on %s...", config.WHISPER_MODEL, config.WHISPER_DEVICE)
    model = WhisperModel(
        config.WHISPER_MODEL,
        device=config.WHISPER_DEVICE,
        compute_type=config.WHISPER_COMPUTE_TYPE,
    )
    logger.info("Transcribing: %s", name)
    segments, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=config.WHISPER_VAD_FILTER,
        hotwords=", ".join(config.VOCABULARY) or None,
        word_timestamps=config.ENABLE_DIARIZATION,
    )
    logger.info("Detected language: %s (prob %.2f)", info.language, info.language_probability)
    return [
        (segment.text.strip(), [(w.start, w.end, w.word) for w in segment.words or []])
        for segment in segments
    ]


def _speaker_turns(audio_path: Path) -> list[tuple[float, float, str]]:
    """Speaker turns for the audio, or [] if labelling is off or unavailable."""
    if not config.ENABLE_DIARIZATION:
        return []
    try:
        from diarizer import diarize
        return diarize(audio_path)
    except Exception:
        # A transcript without speaker labels beats losing the whole video.
        logger.warning("Speaker labelling failed; saving transcript without speaker labels.", exc_info=True)
        return []


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"


def _format_with_speakers(segments: list[Segment], turns: list[tuple[float, float, str]]) -> str:
    """Label each word with the speaker talking at that moment and group into lines."""
    turn_starts = [start for start, _, _ in turns]
    names: dict[str, str] = {}

    def speaker_at(moment: float) -> str:
        # The turn containing this moment, else whichever neighbouring turn is closest.
        after = bisect.bisect_right(turn_starts, moment)
        candidates = turns[max(after - 1, 0):after + 1]
        _, _, label = min(candidates, key=lambda t: max(t[0] - moment, moment - t[1], 0))
        return names.setdefault(label, f"Speaker {len(names) + 1}")

    lines = []
    current_speaker = None
    for _, words in segments:
        # Split the segment wherever the speaker changes mid-sentence.
        runs: list[tuple[str, float, list[str]]] = []
        for start, end, word in words:
            speaker = speaker_at((start + end) / 2)
            if not runs or runs[-1][0] != speaker:
                runs.append((speaker, start, []))
            runs[-1][2].append(word)
        # Word timings are fuzzy at speaker changes, leaving a stray word or two
        # on the wrong side. Fold such fragments into the longer neighbouring run.
        while len(runs) > 1:
            i = min(range(len(runs)), key=lambda r: len(runs[r][2]))
            if len(runs[i][2]) > 2:
                break
            neighbours = [n for n in (i - 1, i + 1) if 0 <= n < len(runs)]
            j = max(neighbours, key=lambda n: len(runs[n][2]))
            first, second = sorted((i, j))
            runs[first] = (runs[j][0], runs[first][1], runs[first][2] + runs[second][2])
            del runs[second]
        for speaker, start, run_words in runs:
            if speaker != current_speaker:
                lines.append(f"\n[{_format_timestamp(start)}] {speaker}:")
                current_speaker = speaker
            lines.append("".join(run_words).strip())
    return "\n".join(lines).strip()


def _transcribe_in_process(video_path: Path) -> str:
    audio_path = extract_audio(video_path)
    try:
        segments = _run_whisper(audio_path, video_path.name)
        turns = _speaker_turns(audio_path)
        if turns:
            return _format_with_speakers(segments, turns)
        return "\n".join(text for text, _ in segments)
    finally:
        audio_path.unlink(missing_ok=True)


def transcribe(video_path: Path) -> str:
    """Transcribe a video file and return the full transcript text.

    The work runs in a child process: the Whisper and diarization libraries keep
    gigabytes of RAM/VRAM for as long as their process lives, and exiting is the
    only way to hand all of it back while the watcher sits idle.
    """
    out_path = Path(tempfile.gettempdir()) / f"{video_path.stem}.transcript.txt"
    try:
        subprocess.run([sys.executable, __file__, str(video_path), str(out_path)], check=True)
        transcript = out_path.read_text(encoding="utf-8")
    finally:
        out_path.unlink(missing_ok=True)
    logger.info("Transcription complete — %d characters.", len(transcript))
    return transcript


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    video, out = sys.argv[1:3]
    Path(out).write_text(_transcribe_in_process(Path(video)), encoding="utf-8")
