import sys
import threading
import signal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from novel_parser.storage import NovelStorage
from novel_parser.parser import NovelMonitor
from novel_parser.api import create_app

storage = None
monitor = None
monitor_thread = None


def setup_directories():
    for directory in ['data', 'docs']:
        Path(directory).mkdir(exist_ok=True)


def start_monitor():
    global storage, monitor, monitor_thread

    storage = NovelStorage(db_path='data/novels.db')
    monitor = NovelMonitor(['docs'], storage)
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
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    setup_directories()
    start_monitor()

    app = create_app(storage)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)


if __name__ == '__main__':
    main()
