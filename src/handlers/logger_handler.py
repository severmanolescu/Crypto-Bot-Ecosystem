"""
Set up a logger for the application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(logger_name="main"):
    """
    Sets up a logger for the application with a rotating file handler.
    Args:
        logger_name (str): The name of the logger. Default is "main".
    """
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Configure root logger
    handler = RotatingFileHandler(
        "logs/" + logger_name + ".log", maxBytes=100_000_000, backupCount=3
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
