import logging

from datetime import datetime, timezone

from sdk.Logger import setup_logger
logger = logging.getLogger(__name__)
logger.info("Load variables started")

def load(file_path="./ConfigurationFiles/variables.json"):
    """
    Load global variables from a JSON file.
    :param file_path: Path to the JSON file.
    :return: Dictionary containing global variables.
    """
    if not os.path.exists(file_path):
        logger.error(f"File '{file_path}' not found. Using default values.")
        print(f"❌ File '{file_path}' not found. Using default values.")
        return {}

    try:
        with open(file_path, "r") as file:
            variables = json.load(file)
            return variables
    except json.JSONDecodeError:
        logger.error(f" Invalid JSON in file '{file_path}'. Using default values.")
        print(f"❌ Invalid JSON in file '{file_path}'. Using default values.")
        return {}
    except Exception as e:
        logger.error(f" Error loading from '{file_path}': {e}. Using default values.")
        print(f"❌ Error loading from '{file_path}': {e}. Using default values.")
        return {}

def save(variables, file_path="./ConfigurationFiles/variables.json"):
    """
    Save global variables to a JSON file.
    """
    try:
        # Convert SEND_HOURS to list for JSON serialization
        if "SEND_HOURS" in variables and isinstance(variables["SEND_HOURS"], set):
            variables["SEND_HOURS"] = list(variables["SEND_HOURS"])

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(variables, file, indent=4)
        print(f"✅ Variables saved to '{file_path}'.")
    except Exception as e:
        logger.error(f" Error saving variables: {e}")
        print(f"❌ Error saving variables: {e}")

def get_json_key_value(file_path, key):
    """
    Safely load a value from a JSON file by key.

    :param file_path: Path to the JSON file.
    :param key: The key to retrieve from the JSON.
    :return: The value if found, else None.
    """
    if not os.path.isfile(file_path):
        logger.warning(f" Warning File does not exist: {file_path}")
        print(f"⚠️ Warning File does not exist: {file_path}")
        return None

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f" Warning: Failed to parse JSON: {e}")
        print(f"⚠️ Warning Failed to parse JSON: {e}")
        return None

    if key not in data:
        logger.warning(f" Warning: Key '{key}' not found in JSON.")
        print(f"⚠️ Warning Key '{key}' not found in JSON.")
        return None

    return data[key]

def get_int_variable(var_name, default=1800, file_path="./ConfigurationFiles/variables.json"):
    """
    Fetch an integer variable from the JSON file.
    If it is a string, attempt to convert it to an integer.
    If invalid or missing, return the default value.
    """
    variables = load(file_path)
    value = variables.get(var_name, default)  # Get the value or default

    # Try to convert strings to integers
    if isinstance(value, int):
        return value
    elif isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            logger.warning(f" Warning: '{var_name}' has an invalid integer format ('{value}'). Using default {default}.")
            print(f"⚠️ Warning: '{var_name}' has an invalid integer format ('{value}'). Using default {default}.")
            return default
    else:
        logger.warning(f" Warning: '{var_name}' is not a valid type. Using default {default}.")
        print(f"⚠️ Warning: '{var_name}' is not a valid type. Using default {default}.")
        return default

def load_portfolio_from_file(file_path = './ConfigurationFiles/portfolio.json'):
    """
    Load portfolio data from a JSON file.
    """
    if not os.path.exists(file_path):
        logger.error(f" Portfolio file '{file_path}' not found. Using an empty portfolio.")
        print(f"❌ Portfolio file '{file_path}' not found. Using an empty portfolio.")
        return {}

    try:
        with open(file_path, "r") as file:
            portfolio = json.load(file)
            logger.info(f" Portfolio loaded from '{file_path}'.")
            print(f"✅ Portfolio loaded from '{file_path}'.")
            return portfolio
    except json.JSONDecodeError:
        logger.error(f" Invalid JSON in portfolio file '{file_path}'. Using an empty portfolio.")
        print(f"❌ Invalid JSON in portfolio file '{file_path}'. Using an empty portfolio.")
        return {}
    except Exception as e:
        logger.error(f" Error loading portfolio from '{file_path}': {e}. Using an empty portfolio.")
        print(f"❌ Error loading portfolio from '{file_path}': {e}. Using an empty portfolio.")
        return {}

def save_data_to_json_file(file_path, data):
    """ Save JSON data to a file. """
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def load_transactions(file_path = './ConfigurationFiles/transactions.json'):
    """ Load transactions from JSON file. """
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_transaction(symbol, action, amount, price, file_path = './ConfigurationFiles/transactions.json'):
    """ Records a transaction in the transactions file. """
    transactions = load_portfolio_from_file(file_path)
    transaction = {
        "symbol": symbol,
        "action": action.upper(),
        "amount": round(amount, 6),
        "price": round(price, 6),
        "total": round(amount * price, 2),
        "timestamp": datetime.now(timezone.utc).isoformat()  # Fixes deprecation warning
    }
    transactions.append(transaction)
    save_data_to_json_file(file_path, transactions)

def load_keyword_list(file_path="./ConfigurationFiles/keywords.json"):
    """
    Load a list of keywords from a JSON file.
    Returns an empty list if the file is missing or invalid.
    """
    if not os.path.exists(file_path):
        logger.error(f" File '{file_path}' not found. Returning an empty list.")
        print(f"❌ File '{file_path}' not found. Returning an empty list.")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            keywords = json.load(file)
            if isinstance(keywords, list):
                print(f"✅ Loaded {len(keywords)} keywords from '{file_path}'.")
                return keywords
            else:
                logger.warning(f" Warning: Expected a list in '{file_path}', but got something else. Returning empty list.")
                print(f"⚠️ Warning: Expected a list in '{file_path}', but got something else. Returning empty list.")
                return []
    except json.JSONDecodeError:
        logger.error(f" Invalid JSON in '{file_path}'. Returning empty list.")
        print(f"❌ Invalid JSON in '{file_path}'. Returning empty list.")
        return []
    except Exception as e:
        logger.error(f" Error loading '{file_path}': {e}. Returning empty list.")
        print(f"❌ Error loading '{file_path}': {e}. Returning empty list.")
        return []

def load_symbol_to_id(file_path="./ConfigurationFiles/symbol_to_id.json"):
    """
    Load the symbol-to-ID mapping from a JSON file.
    :param file_path: Path to the JSON file.
    :return: Dictionary containing symbol-to-ID mappings.
    """
    if not os.path.exists(file_path):
        logger.error(f" Symbol-to-ID file '{file_path}' not found. Using an empty mapping.")
        print(f"❌ Symbol-to-ID file '{file_path}' not found. Using an empty mapping.")
        return {}

    try:
        with open(file_path, "r") as file:
            symbol_to_id = json.load(file)
            print(f"✅ Symbol-to-ID mapping loaded from '{file_path}'.")
            return symbol_to_id
    except json.JSONDecodeError:
        logger.error(f" Invalid JSON in symbol-to-ID file '{file_path}'. Using an empty mapping.")
        print(f"❌ Invalid JSON in symbol-to-ID file '{file_path}'. Using an empty mapping.")
        return {}
    except Exception as e:
        logger.error(f" Error loading symbol-to-ID mapping from '{file_path}': {e}. Using an empty mapping.")
        print(f"❌ Error loading symbol-to-ID mapping from '{file_path}': {e}. Using an empty mapping.")
        return {}

def load_keywords(file_path="./ConfigurationFiles/keywords.json"):
    """
    Load keywords from a JSON file.
    :param file_path: Path to the JSON file.
    :return: List of keywords.
    """
    if not os.path.exists(file_path):
        logger.error(f" Keywords file '{file_path}' not found. Using an empty list.")
        print(f"❌ Keywords file '{file_path}' not found. Using an empty list.")
        return []

    try:
        with open(file_path, "r") as file:
            keywords = json.load(file)
            print(f"✅ Keywords loaded from '{file_path}'.")
            return keywords
    except json.JSONDecodeError:
        logger.error(f" Invalid JSON in keywords file '{file_path}'. Using an empty list.")
        print(f"❌ Invalid JSON in keywords file '{file_path}'. Using an empty list.")
        return []
    except Exception as e:
        logger.error(f" Error loading keywords from '{file_path}': {e}. Using an empty list.")
        print(f"❌ Error loading keywords from '{file_path}': {e}. Using an empty list.")
        return []

def save_keywords(keywords, file_path="./ConfigurationFiles/keywords.json"):
    """
    Save keywords to a JSON file.
    :param keywords: List of keywords to save.
    :param file_path: Path to the JSON file.
    """
    try:
        with open(file_path, "w") as file:
            json.dump(keywords, file, indent=4)
        print(f"✅ Keywords saved to '{file_path}'.")
    except Exception as e:
        logger.error(f" Error saving keywords to '{file_path}': {e}.")
        print(f"❌ Error saving keywords to '{file_path}': {e}.")


import json
import os


def get_all_symbols(file_path = ''):
    """
    Reads a list of transactions from a JSON file and returns a list of unique symbols.

    :param file_path: Path to the JSON file containing transaction data.
    :return: List of unique symbols used in the transactions.
    """
    transactions = load_transactions()

    if not isinstance(transactions, list) or len(transactions) == 0:
        logger.warning("Warning: JSON file is empty or not a list of transactions.")
        print("⚠️ Warning: JSON file is empty or not a list of transactions.")
        return []

    symbols = set()  # Use set to avoid duplicates

    for tx in transactions:
        if isinstance(tx, dict) and "symbol" in tx:
            symbols.add(tx["symbol"])

    return list(symbols)
