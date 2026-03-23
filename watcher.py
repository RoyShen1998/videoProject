import logging
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import config
from file_manager import wait_for_stable_file

logger = logging.getLogger(__name__)


class VideoHandler(FileSystemEventHandler):
    def __init__(self, process_callback):
        self.process_callback = process_callback

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in config.VIDEO_EXTENSIONS:
            logger.info("New video detected: %s", path.name)
            wait_for_stable_file(path)
            self.process_callback(path)


def start_watching(process_callback) -> Observer:
    """Start watching newVideo/ for new video files. Returns the observer."""
    handler = VideoHandler(process_callback)
    observer = Observer()
    observer.schedule(handler, str(config.NEW_VIDEO_DIR), recursive=False)
    observer.start()
    logger.info("Watching %s for new videos...", config.NEW_VIDEO_DIR)
    return observer
