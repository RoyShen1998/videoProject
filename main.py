import logging
import time
from pathlib import Path

import config
from watcher import start_watching
from transcriber import transcribe
from summarizer import summarize
from file_manager import (
    generate_base_name,
    save_transcript,
    save_summary,
    move_video,
    cleanup_old_files,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def process_video(video_path: Path):
    """Full pipeline: transcribe → summarize → save & move files."""
    logger.info("=" * 60)
    logger.info("Processing: %s", video_path.name)

    try:
        # Step 1: Transcribe
        transcript = transcribe(video_path)

        # Step 2: Summarize with Claude
        title, summary = summarize(transcript)

        # Step 3: Save files with descriptive name
        base_name = generate_base_name(title)
        save_transcript(transcript, base_name)
        save_summary(summary, base_name)
        move_video(video_path, base_name)

        # Step 4: Cleanup old processed videos
        cleanup_old_files()

        logger.info("Done processing: %s → %s", video_path.name, base_name)
    except Exception:
        logger.exception("Failed to process %s", video_path.name)

    logger.info("=" * 60)


def process_existing_files():
    """Process any video files already sitting in newVideo/."""
    for f in config.NEW_VIDEO_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in config.VIDEO_EXTENSIONS:
            logger.info("Found existing video: %s", f.name)
            process_video(f)


def main():
    logger.info("Meeting Video Summarization Pipeline starting...")

    # Run cleanup on startup
    cleanup_old_files()

    # Process any videos already in the folder
    process_existing_files()

    # Watch for new videos
    observer = start_watching(process_video)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        observer.stop()

    observer.join()
    logger.info("Stopped.")


if __name__ == "__main__":
    main()
