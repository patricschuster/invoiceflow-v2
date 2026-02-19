import os
from dotenv import load_dotenv

load_dotenv()

WATCH_PATH = os.getenv("WATCH_PATH", "/app/data/incoming")
PROCESSING_PATH = os.getenv("PROCESSING_PATH", "/app/data/processing")
ERROR_PATH = os.getenv("ERROR_PATH", "/app/data/error")
API_URL = os.getenv("API_URL", "http://backend:8000")
WATCHER_API_KEY = os.getenv("WATCHER_API_KEY", "")
