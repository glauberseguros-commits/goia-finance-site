from pathlib import Path
import os

APP_NAME = "GOIA Finance Platform"
APP_VERSION = "1.0.0"

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.getenv("GOIA_DATA_DIR", ROOT_DIR / "data"))
LOG_DIR = Path(os.getenv("GOIA_LOG_DIR", ROOT_DIR / "logs"))
TEMP_DIR = Path(os.getenv("GOIA_TEMP_DIR", ROOT_DIR / "temp"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
