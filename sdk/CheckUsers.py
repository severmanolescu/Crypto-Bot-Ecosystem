import logging

from datetime import datetime

logger = logging.getLogger("CheckUsers.py")

logging.basicConfig(filename='log.log', level=logging.INFO)
logger.info(f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Started!')

from sdk import LoadVariables as load_variables

def check_if_special_user(user_id):
    """
    Check if the given user_id is in the special user list from the config file.

    :param user_id: The Telegram user ID to check.
    :return: True if user_id is in the special user list, otherwise False.
    """
    try:
        variables = load_variables.load()
        special_users = variables.get("TELEGRAM_CHAT_ID_FULL_DETAILS", [])

        # Ensure special_users is a list or set
        if not isinstance(special_users, (list, set)):
            logger.info(f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Invalid format for TELEGRAM_CHAT_ID_FULL_DETAILS. Expected list or set.')
            print("❌ Invalid format for TELEGRAM_CHAT_ID_FULL_DETAILS. Expected list or set.")
            return False

        # Ensure user_id and stored IDs are the same type
        user_id = str(user_id)  # Convert to string to match JSON-stored values

        return user_id in map(str, special_users)  # Convert all IDs to string before checking

    except Exception as e:
        logger.info(f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error checking special user: {e}')
        print(f"❌ Error checking special user: {e}")
        return False
