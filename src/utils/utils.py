"""
Utility functions for handling requests and checking user permissions.
"""

import logging

import requests

import src.handlers.load_variables_handler

logger = logging.getLogger(__name__)
logger.info("Alerts script started")


def check_requests(url, headers=None, params=None):
    """
    Check if the request to the given URL is successful and return the JSON response.
    Args:
        url (str): The URL to send the request to.
        headers (dict, optional): Headers to include in the request.
        params (dict, optional): Query parameters to include in the request.
    Returns:
        dict: The JSON response from the request if successful, otherwise None.
    """
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        return response.json()
    # pylint: disable=broad-except
    except Exception as e:
        logger.error("Exception while requests from %s: %s", url, e)
        print(f"Exception while requests from {url}: {e}")
    return None


def format_change(change):
    """
    Format the change percentage for display in Telegram messages.
    Args:
        change (float): The change percentage to format.
    """
    if change is None:
        return "N/A"
    if change < 0:
        return f"🔴 {change:.2f}%"  # Negative change in monospace

    return f"🟢 +{change:.2f}%"  # Positive change in monospace


def check_if_special_user(user_id):
    """
    Check if the given user_id is in the special user list from the config file.
    Args:
        user_id (int or str): The user ID to check.
    """
    try:
        variables = src.handlers.load_variables_handler.load()
        special_users = variables.get("TELEGRAM_CHAT_ID_FULL_DETAILS", [])

        # Ensure special_users is a list or set
        if not isinstance(special_users, (list, set)):
            logger.info(
                "Invalid format for TELEGRAM_CHAT_ID_FULL_DETAILS. Expected list or set."
            )
            print(
                "❌ Invalid format for TELEGRAM_CHAT_ID_FULL_DETAILS. Expected list or set."
            )
            return False

        # Ensure user_id and stored IDs are the same type
        user_id = str(user_id)  # Convert to string to match JSON-stored values

        return user_id in map(
            str, special_users
        )  # Convert all IDs to string before checking

    # pylint: disable=broad-except
    except Exception as e:
        logger.info(" Error checking special user: %s", e)
        print(f"❌ Error checking special user: {e}")
        return False
