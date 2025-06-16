"""
Test logger setup module
"""

# pylint: disable=redefined-outer-name,unused-argument


import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from src.handlers.logger_handler import setup_logger

LOGS_PATHS = "./tests/test_files"
LOG_FILE = "main.log"
MAIN_LOG = os.path.join(LOGS_PATHS, LOG_FILE)


@pytest.fixture
def clean_logs_dir():
    """Fixture to ensure a clean logs directory state"""
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.close()  # Close handler to release file handle
    root_logger.handlers.clear()

    logs_dir = Path(LOGS_PATHS)
    if logs_dir.exists():
        for file in logs_dir.glob("*.*"):
            file.unlink()
        logs_dir.rmdir()
    yield
    # Cleanup after tests
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.close()  # Close handler to release file handle
    root_logger.handlers.clear()

    if logs_dir.exists():
        for file in logs_dir.glob("*.*"):
            file.unlink()
        logs_dir.rmdir()


def test_setup_logging_creates_directory(clean_logs_dir):
    """Test that setup_logging creates the logs directory"""
    setup_logger(logs_dir=LOGS_PATHS)
    assert os.path.exists(LOGS_PATHS)
    assert os.path.isdir(LOGS_PATHS)


def test_setup_logging_creates_log_file(clean_logs_dir):
    """Test that setup_logging creates the log file"""
    setup_logger(logs_dir=LOGS_PATHS)
    assert os.path.exists(MAIN_LOG)


def test_logger_configuration(clean_logs_dir):
    """Test logger configuration settings"""
    setup_logger(logs_dir=LOGS_PATHS)
    root_logger = logging.getLogger()

    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) > 0

    handler = root_logger.handlers[0]
    assert isinstance(handler, RotatingFileHandler)
    assert handler.baseFilename.endswith(LOG_FILE)
    assert handler.maxBytes == 100_000_000
    assert handler.backupCount == 3


def test_log_message_format(clean_logs_dir):
    """Test that log messages are properly formatted"""
    setup_logger(logs_dir=LOGS_PATHS)
    test_message = "Test log message"
    logging.getLogger().info(test_message)

    with open(MAIN_LOG, "r", encoding="utf-8") as log_file:
        log_content = log_file.read()
        assert test_message in log_content
        # Check format parts
        assert " | INFO | root | " in log_content
