import re
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def sanitize_filename(title: str) -> str:
    """Convert a title string into a safe filename slug."""
    title = title.strip().lower()
    title = re.sub(r"[^\w\s-]", "", title)
    title = re.sub(r"[\s_]+", "-", title)
    title = title.strip("-")
    return title or "meeting"


def generate_base_name(title: str) -> str:
    """Generate a descriptive base filename from the title + date."""
    slug = sanitize_filename(title)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"{date_str}_{slug}"


def save_transcript(transcript: str, base_name: str) -> Path:
    """Save transcript text to the transcript directory."""
    path = config.TRANSCRIPT_DIR / f"{base_name}.txt"
    path.write_text(transcript, encoding="utf-8")
    logger.info("Saved transcript: %s", path.name)
    return path


def save_summary(summary: str, base_name: str) -> Path:
    """Save summary markdown to the summary directory."""
    path = config.SUMMARY_DIR / f"{base_name}.md"
    path.write_text(summary, encoding="utf-8")
    logger.info("Saved summary: %s", path.name)
    return path


def move_video(video_path: Path, base_name: str) -> Path:
    """Move the original video to processedVideo with the descriptive name."""
    dest = config.PROCESSED_VIDEO_DIR / f"{base_name}{video_path.suffix}"
    video_path.rename(dest)
    logger.info("Moved video to: %s", dest.name)
    return dest


def cleanup_old_files():
    """Delete files in processedVideo/ older than MAX_FILE_AGE_DAYS."""
    cutoff = time.time() - (config.MAX_FILE_AGE_DAYS * 86400)
    deleted = 0
    for f in config.PROCESSED_VIDEO_DIR.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink()
            logger.info("Deleted old file: %s", f.name)
            deleted += 1
    if deleted:
        logger.info("Cleanup: deleted %d old file(s).", deleted)


def wait_for_stable_file(path: Path):
    """Poll file size until it stops changing (file copy complete)."""
    logger.info("Waiting for file to stabilize: %s", path.name)
    prev_size = -1
    stable_count = 0
    while stable_count < config.FILE_STABLE_CHECKS:
        try:
            size = path.stat().st_size
        except OSError:
            time.sleep(config.FILE_STABLE_INTERVAL)
            continue
        if size == prev_size and size > 0:
            stable_count += 1
        else:
            stable_count = 0
        prev_size = size
        time.sleep(config.FILE_STABLE_INTERVAL)
    logger.info("File is stable: %s (%d bytes)", path.name, prev_size)
