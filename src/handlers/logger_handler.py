"""
Set up a logger for the application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(logs_dir=None, file_name="main.log"):
    """
    Setup logging configuration for the application.
    """
    # Create logs directory if it doesn't exist
    logs_dir = logs_dir or "logs"
    main_log = os.path.join(logs_dir, file_name)

    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Configure root logger
    handler = RotatingFileHandler(main_log, maxBytes=100_000_000, backupCount=3)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
