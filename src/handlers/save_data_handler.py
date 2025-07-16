"""
Save data handler module.
This module provides functions to save global variables, transactions, and keywords to JSON files.
"""

import json
import logging
import os
from datetime import datetime, timezone

from src.handlers.load_variables_handler import load_portfolio_from_file

logger = logging.getLogger(__name__)
logger.info("Save data started")


def save_variables_json(variables, file_path="./config/variables.json"):
    """
    Save global variables to a JSON file.
    Args:
        variables (dict): A dictionary containing the global variables to save.
        file_path (str): Path to the JSON file where variables will be saved.
    """
    try:
        # Convert SEND_HOURS to list for JSON serialization
        if "SEND_HOURS" in variables and isinstance(variables["SEND_HOURS"], set):
            variables["SEND_HOURS"] = list(variables["SEND_HOURS"])

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(variables, file, indent=4)
        logger.info("✅ Variables saved to %s.", file_path)
    # pylint:disable=broad-exception-caught
    except Exception as e:
        logger.error(" Error saving variables: %s", e)
        print("❌ Error saving variables: ", e)


def save_data_to_json_file(file_path, data):
    """
    Save JSON data to a file.
    Args:
        file_path (str): Path to the JSON file where data will be saved.
        data (dict or list): Data to save in JSON format.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def save_transaction(
    symbol, action, amount, price, file_path="./config/transactions.json"
):
    """
    Records a transaction in the transactions file.
    Args:
        symbol (str): The stock symbol for the transaction.
        action (str): The action type, either 'buy' or 'sell'.
        amount (float): The amount of shares involved in the transaction.
        price (float): The price per share at the time of the transaction.
        file_path (str): Path to the JSON file where transactions will be saved.
    """
    transactions = load_portfolio_from_file(file_path)
    transaction = {
        "symbol": symbol,
        "action": action.upper(),
        "amount": round(amount, 6),
        "price": round(price, 6),
        "total": round(amount * price, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    transactions.append(transaction)
    save_data_to_json_file(file_path, transactions)


def save_keywords(keywords, file_path="./config/keywords.json"):
    """
    Save keywords to a JSON file.
    Args:
        keywords (list): A list of keywords to save.
        file_path (str): Path to the JSON file where keywords will be saved.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(keywords, file, indent=4)
        print(f"✅ Keywords saved to '{file_path}'.")
    # pylint:disable=broad-exception-caught
    except Exception as e:
        logger.error(" Error saving keywords to %s: %s.", file_path, e)
        print(f"❌ Error saving keywords to '{file_path}': {e}.")
