import os
import argparse
import logging
import threading
from pathlib import Path

from app.storage.novel_storage import NovelStorage
from app.parser.file_monitor import NovelMonitor
from app.api.novel_api import NovelAPI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('novel_system.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Novel Parser and API System')
    
    parser.add_argument(
        '--novel-dirs', 
        nargs='+', 
        default=['docs'],
        help='Directories to monitor for novel files (default: docs)'
    )
    
    parser.add_argument(
        '--db-path', 
        default='novels.db',
        help='Path to the SQLite database file (default: novels.db)'
    )
    
    parser.add_argument(
        '--host', 
        default='0.0.0.0',
        help='Host to bind the API server (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000,
        help='Port to bind the API server (default: 5000)'
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # Create storage
    storage = NovelStorage(db_path=args.db_path)
    
    # Create API
    api = NovelAPI(storage, host=args.host, port=args.port)
    
    # Create monitor
    monitor = NovelMonitor(args.novel_dirs, storage)
    
    # Start monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor.start, daemon=True)
    monitor_thread.start()
    
    # Start API (blocking)
    try:
        api.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        monitor.stop()

if __name__ == '__main__':
    main()
