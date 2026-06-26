import logging
from core.config import LOG_DIR

logging.basicConfig(
    filename=LOG_DIR / "goia.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("GOIA")
