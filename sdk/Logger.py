import logging
from logging.handlers import RotatingFileHandler

def setup_logger(log_file):
    handler = RotatingFileHandler(log_file, maxBytes=100_000_000, backupCount=3)
    logging.basicConfig(
        handlers=[handler],
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    return logging.getLogger()
