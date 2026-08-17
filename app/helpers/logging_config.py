# logging_config.py

import logging
import colorlog
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)

console_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s | %(levelname)-8s | "
    "%(name)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
def setup_logging():
    formatter = logging.Formatter(LOG_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # File Handler
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    # Reduce noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)