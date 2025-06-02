import os
import logging

from logging.handlers import RotatingFileHandler

def setup_logger(logger_name='main'):
    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Configure root logger
    handler = RotatingFileHandler('logs/' + logger_name + '.log', maxBytes=100_000_000, backupCount=3)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
