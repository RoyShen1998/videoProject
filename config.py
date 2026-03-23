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

# Supported video extensions
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi"}

# File stability check (seconds between size polls)
FILE_STABLE_INTERVAL = 2
FILE_STABLE_CHECKS = 3

# Auto-delete processed videos older than this many days
MAX_FILE_AGE_DAYS = 30
