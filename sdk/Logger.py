import logging
from logging.handlers import RotatingFileHandler


def setup_logger(log_file):
    # Create a logger with a specific name
    logger = logging.getLogger('Crypto-Articles_Bots')

    # Set the level
    logger.setLevel(logging.INFO)

    # Create the handler
    handler = RotatingFileHandler(log_file, maxBytes=100_000_000, backupCount=3)

    # Create a formatter and set it on the handler
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger