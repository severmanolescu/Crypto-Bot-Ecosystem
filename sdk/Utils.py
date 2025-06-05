import logging

import requests

from sdk import load_variables_handler as LoadVariables

logger = logging.getLogger(__name__)
logger.info("Alerts script started")


def check_requests(url, headers=None, params=None):
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json()
    except Exception as e:
        logger.error(f"Exception while requests form {url}")
        print(f"Exception while requests form {url}")
    return None


def format_change(change):
    if change is None:
        return "N/A"
    if change < 0:
        return f"🔴 {change:.2f}%"  # Negative change in monospace
    else:
        return f"🟢 +{change:.2f}%"  # Positive change in monospace


def check_if_special_user(user_id):
    """
    Check if the given user_id is in the special user list from the config file.

    :param user_id: The Telegram user ID to check.
    :return: True if user_id is in the special user list, otherwise False.
    """
    try:
        variables = LoadVariables.load()
        special_users = variables.get("TELEGRAM_CHAT_ID_FULL_DETAILS", [])

        # Ensure special_users is a list or set
        if not isinstance(special_users, (list, set)):
            logger.info(
                f"Invalid format for TELEGRAM_CHAT_ID_FULL_DETAILS. Expected list or set."
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

    except Exception as e:
        logger.info(f" Error checking special user: {e}")
        print(f"❌ Error checking special user: {e}")
        return False
