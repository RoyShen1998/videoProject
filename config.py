from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent

# Folder paths
NEW_VIDEO_DIR = BASE_DIR / "newVideo"
TRANSCRIPT_DIR = BASE_DIR / "textTranscript"
SUMMARY_DIR = BASE_DIR / "summary"
PROCESSED_VIDEO_DIR = BASE_DIR / "processedVideo"

# Whisper settings
WHISPER_MODEL = "large-v3"
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE_TYPE = "float16"
# Skip non-speech audio so Whisper doesn't invent text ("Thank you.") over silence.
WHISPER_VAD_FILTER = True

# Product names, systems and jargon that come up in meetings. Whisper is nudged
# toward these spellings and the summarizer uses them to fix mis-heard terms.
VOCABULARY = []

# Speaker labels ("Speaker 1: ...") via pyannote. Needs a Hugging Face token with
# the model's terms accepted; if unavailable the transcript is saved unlabelled.
ENABLE_DIARIZATION = True
DIARIZATION_MODEL = "pyannote/speaker-diarization-community-1"

# Claude CLI settings (model used to summarize transcripts)
CLAUDE_MODEL = "claude-fable-5-2"

# Supported video extensions
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi"}

# File stability check (seconds between size polls)
FILE_STABLE_INTERVAL = 2
FILE_STABLE_CHECKS = 3

# Auto-delete processed videos older than this many days
MAX_FILE_AGE_DAYS = 30
