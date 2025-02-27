import logging

from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('log.log', maxBytes=100_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)

from sdk import LoadVariables as LoadVariables

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
            logging.info(f'Invalid format for TELEGRAM_CHAT_ID_FULL_DETAILS. Expected list or set.')
            print("❌ Invalid format for TELEGRAM_CHAT_ID_FULL_DETAILS. Expected list or set.")
            return False

        # Ensure user_id and stored IDs are the same type
        user_id = str(user_id)  # Convert to string to match JSON-stored values

        return user_id in map(str, special_users)  # Convert all IDs to string before checking

    except Exception as e:
        logging.info(f' Error checking special user: {e}')
        print(f"❌ Error checking special user: {e}")
        return False
