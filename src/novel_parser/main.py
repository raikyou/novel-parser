import sys
import threading
import signal
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv not available, continue with system env vars

sys.path.insert(0, str(Path(__file__).parent.parent))

from novel_parser.storage import DatabaseFactory
from novel_parser.parser import NovelMonitor
from novel_parser.api import create_app
from novel_parser.config import Config

storage = None
monitor = None
monitor_thread = None


def setup_directories():
    for directory in ['data', Config.DOCS_DIR]:
        Path(directory).mkdir(exist_ok=True)


def create_storage():
    """Create storage instance based on configuration."""
    if Config.DATABASE_TYPE == "sqlite":
        return DatabaseFactory.create_database("sqlite", db_path=Config.SQLITE_DB_PATH)
    elif Config.DATABASE_TYPE == "postgresql":
        return DatabaseFactory.create_database("postgresql", connection_url=Config.DATABASE_URL)
    else:
        raise ValueError(f"Unsupported database type: {Config.DATABASE_TYPE}")


def start_monitor():
    global storage, monitor, monitor_thread

    storage = create_storage()
    monitor = NovelMonitor([Config.DOCS_DIR], storage)
    monitor_thread = threading.Thread(target=monitor.start, daemon=True)
    monitor_thread.start()


def stop_monitor():
    global monitor
    if monitor:
        monitor.stop()


def signal_handler(_signum, _frame):
    stop_monitor()
    sys.exit(0)


def main():
    # Validate configuration
    Config.validate_config()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    setup_directories()
    start_monitor()

    app = create_app(storage)

    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)


if __name__ == '__main__':
    main()
