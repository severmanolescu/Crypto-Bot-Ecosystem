import requests

from sdk.Logger import setup_logger

logger = setup_logger("utils.log")
logger.info("Alerts script started")

def check_requests(url, headers = None, params = None):
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

