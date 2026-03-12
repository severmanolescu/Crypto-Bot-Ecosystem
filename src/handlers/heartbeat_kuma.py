"""
Sends a heartbeat to Uptime Kuma every minute to keep the monitor alive.
"""

# pylint:disable=bare-except


import time

import requests


def heartbeat(uptime_kuma_url):
    """
    Sends a heartbeat to Uptime Kuma every minute to keep the monitor alive.
    Args:
        uptime_kuma_url (str): The URL of the Uptime Kuma heartbeat endpoint.
    """
    if not uptime_kuma_url or uptime_kuma_url == "":
        print("Uptime Kuma URL not set. Heartbeat will not be sent.")
        return

    while True:
        try:
            requests.get(uptime_kuma_url, timeout=10)
        except:
            pass
        time.sleep(60)
