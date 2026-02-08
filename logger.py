import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger  # чтобы не дублировать хендлеры

    # INFO лог
    info_handler = RotatingFileHandler(
        f"{LOG_DIR}/info.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    info_handler.setLevel(logging.INFO)

    # ERROR лог
    error_handler = RotatingFileHandler(
        f"{LOG_DIR}/error.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    info_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    logger.addHandler(info_handler)
    logger.addHandler(error_handler)

    return logger