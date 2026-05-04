import logging
import os
from datetime import datetime

log_dir = "./logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"nte_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)

logger = logging.getLogger("NTE")
