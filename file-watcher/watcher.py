import logging
import shutil
import time
from datetime import datetime
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from config import ERROR_PATH, PROCESSING_PATH, WATCH_PATH
from processors.pdf_processor import PDFProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("watcher")

ALLOWED_EXTENSIONS = {".pdf", ".xml"}


class InvoiceEventHandler(FileSystemEventHandler):
    """Handles new files arriving in the watch folder."""

    def on_created(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)
        if src.suffix.lower() not in ALLOWED_EXTENSIONS:
            logger.debug(f"Ignoring non-invoice file: {src.name}")
            return

        logger.info(f"New file detected: {src.name}")

        # Wait for file to be fully written
        time.sleep(2)

        self._process_file(src)

    def _process_file(self, src: Path):
        """Move file to processing and call backend API."""
        # Build destination path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = Path(PROCESSING_PATH) / f"{timestamp}_{src.name}"

        try:
            # Ensure directories exist
            dest.parent.mkdir(parents=True, exist_ok=True)
            Path(ERROR_PATH).mkdir(parents=True, exist_ok=True)

            # Move to processing
            shutil.move(str(src), str(dest))
            logger.info(f"Moved to processing: {dest.name}")

            # Call backend
            PDFProcessor.process(dest)

        except Exception as e:
            logger.error(f"Failed to process {src.name}: {e}")
            self._move_to_error(dest if dest.exists() else src, str(e))

    def _move_to_error(self, file_path: Path, reason: str):
        """Move file to error folder."""
        try:
            error_dir = Path(ERROR_PATH)
            error_dir.mkdir(parents=True, exist_ok=True)
            error_dest = error_dir / file_path.name
            shutil.move(str(file_path), str(error_dest))
            logger.warning(f"Moved to error/: {file_path.name} — reason: {reason}")
        except Exception as e:
            logger.error(f"Could not move file to error/: {e}")


def main():
    watch_path = Path(WATCH_PATH)
    watch_path.mkdir(parents=True, exist_ok=True)
    Path(PROCESSING_PATH).mkdir(parents=True, exist_ok=True)
    Path(ERROR_PATH).mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting file watcher on: {watch_path}")

    event_handler = InvoiceEventHandler()
    observer = PollingObserver(timeout=10)  # Poll every 10 seconds
    observer.schedule(event_handler, str(watch_path), recursive=False)
    observer.start()

    logger.info("Watching for new invoice files... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
    finally:
        observer.stop()
        observer.join()
        logger.info("Watcher stopped.")


if __name__ == "__main__":
    main()
