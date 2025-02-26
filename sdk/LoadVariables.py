import os
import json
import logging

from datetime import datetime

from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('log.log', maxBytes=100_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
def load(file_path="./ConfigurationFiles/variables.json"):
    """
    Load global variables from a JSON file.
    :param file_path: Path to the JSON file.
    :return: Dictionary containing global variables.
    """
    if not os.path.exists(file_path):
        logging.info(f" Variables file '{file_path}' not found. Using default values.")
        print(f"❌ Variables file '{file_path}' not found. Using default values.")
        return {}

    try:
        with open(file_path, "r") as file:
            variables = json.load(file)
            print(f"✅ Variables loaded from '{file_path}'.")
            return variables
    except json.JSONDecodeError:
        logging.info(f" Invalid JSON in variables file '{file_path}'. Using default values.")
        print(f"❌ Invalid JSON in variables file '{file_path}'. Using default values.")
        return {}
    except Exception as e:
        logging.info(f" Error loading variables from '{file_path}': {e}. Using default values.")
        print(f"❌ Error loading variables from '{file_path}': {e}. Using default values.")
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
        logging.info(f" Error saving variables: {e}")
        print(f"❌ Error saving variables: {e}")

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
            logging.info(f" Warning: '{var_name}' has an invalid integer format ('{value}'). Using default {default}.")
            print(f"⚠️ Warning: '{var_name}' has an invalid integer format ('{value}'). Using default {default}.")
            return default
    else:
        logging.info(f" Warning: '{var_name}' is not a valid type. Using default {default}.")
        print(f"⚠️ Warning: '{var_name}' is not a valid type. Using default {default}.")
        return default

def load_keyword_list(file_path="./ConfigurationFiles/keywords.json"):
    """
    Load a list of keywords from a JSON file.
    Returns an empty list if the file is missing or invalid.
    """
    if not os.path.exists(file_path):
        logging.info(f" File '{file_path}' not found. Returning an empty list.")
        print(f"❌ File '{file_path}' not found. Returning an empty list.")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            keywords = json.load(file)
            if isinstance(keywords, list):
                print(f"✅ Loaded {len(keywords)} keywords from '{file_path}'.")
                return keywords
            else:
                logging.info(f" Warning: Expected a list in '{file_path}', but got something else. Returning empty list.")
                print(f"⚠️ Warning: Expected a list in '{file_path}', but got something else. Returning empty list.")
                return []
    except json.JSONDecodeError:
        logging.info(f" Invalid JSON in '{file_path}'. Returning empty list.")
        print(f"❌ Invalid JSON in '{file_path}'. Returning empty list.")
        return []
    except Exception as e:
        logging.info(f" Error loading '{file_path}': {e}. Returning empty list.")
        print(f"❌ Error loading '{file_path}': {e}. Returning empty list.")
        return []

def load_symbol_to_id(file_path="./ConfigurationFiles/symbol_to_id.json"):
    """
    Load the symbol-to-ID mapping from a JSON file.
    :param file_path: Path to the JSON file.
    :return: Dictionary containing symbol-to-ID mappings.
    """
    if not os.path.exists(file_path):
        logging.info(f" Symbol-to-ID file '{file_path}' not found. Using an empty mapping.")
        print(f"❌ Symbol-to-ID file '{file_path}' not found. Using an empty mapping.")
        return {}

    try:
        with open(file_path, "r") as file:
            symbol_to_id = json.load(file)
            print(f"✅ Symbol-to-ID mapping loaded from '{file_path}'.")
            return symbol_to_id
    except json.JSONDecodeError:
        logging.info(f" Invalid JSON in symbol-to-ID file '{file_path}'. Using an empty mapping.")
        print(f"❌ Invalid JSON in symbol-to-ID file '{file_path}'. Using an empty mapping.")
        return {}
    except Exception as e:
        logging.info(f" Error loading symbol-to-ID mapping from '{file_path}': {e}. Using an empty mapping.")
        print(f"❌ Error loading symbol-to-ID mapping from '{file_path}': {e}. Using an empty mapping.")
        return {}

def load_keywords(file_path="./ConfigurationFiles/keywords.json"):
    """
    Load keywords from a JSON file.
    :param file_path: Path to the JSON file.
    :return: List of keywords.
    """
    if not os.path.exists(file_path):
        logging.info(f" Keywords file '{file_path}' not found. Using an empty list.")
        print(f"❌ Keywords file '{file_path}' not found. Using an empty list.")
        return []

    try:
        with open(file_path, "r") as file:
            keywords = json.load(file)
            print(f"✅ Keywords loaded from '{file_path}'.")
            return keywords
    except json.JSONDecodeError:
        logging.info(f" Invalid JSON in keywords file '{file_path}'. Using an empty list.")
        print(f"❌ Invalid JSON in keywords file '{file_path}'. Using an empty list.")
        return []
    except Exception as e:
        logging.info(f" Error loading keywords from '{file_path}': {e}. Using an empty list.")
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
        logging.info(f" Error saving keywords to '{file_path}': {e}.")
        print(f"❌ Error saving keywords to '{file_path}': {e}.")
