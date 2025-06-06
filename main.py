import os
import logging
import threading

from app.storage.novel_storage import NovelStorage
from app.parser.file_monitor import NovelMonitor
from app.api.novel_api import create_app

# Create logs and data directories if they don't exist
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'novel_system.log'))
    ]
)
logger = logging.getLogger(__name__)

# Global variables for storage and monitor
storage = None
monitor = None
monitor_thread = None


def start_monitor():
    """Start the file monitor."""
    global storage, monitor, monitor_thread

    logger.info("Starting Novel Parser System...")

    # Create storage with fixed path
    storage = NovelStorage(db_path='data/novels.db')

    # Create monitor with fixed directory
    monitor = NovelMonitor(['docs'], storage)

    # Start monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor.start, daemon=True)
    monitor_thread.start()

    logger.info("Novel Parser System started successfully")


def stop_monitor():
    """Stop the file monitor."""
    global monitor
    logger.info("Shutting down Novel Parser System...")
    if monitor:
        monitor.stop()
    logger.info("Novel Parser System shut down")


def main():
    """Main entry point for the application."""
    import uvicorn

    # Start monitor
    start_monitor()

    # Create FastAPI app
    app = create_app(storage)

    # Start server
    logger.info("Starting Novel API server on 0.0.0.0:5001")
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=5001,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        stop_monitor()


if __name__ == '__main__':
    main()
