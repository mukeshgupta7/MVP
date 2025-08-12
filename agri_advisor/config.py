from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLES_DIR = DATA_DIR / "samples"
DB_PATH = DATA_DIR / "knowledge.db"
INDEX_DIR = DATA_DIR / "index"

SUPPORTED_LANGS = {"en", "hi"}
DEFAULT_LANG = "en"

# Retrieval config
MAX_DOCS = 8

# Simple irrigation heuristics
RAINFALL_WINDOW_DAYS = 3
RAINFALL_THRESHOLD_MM = 15.0
HIGH_TEMP_C = 35.0