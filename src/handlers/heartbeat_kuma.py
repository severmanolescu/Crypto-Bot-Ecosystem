import time

import requests


def heartbeat(uptime_kuma_url):
    if not uptime_kuma_url or uptime_kuma_url == "":
        print("Uptime Kuma URL not set. Heartbeat will not be sent.")
        return

    while True:
        try:
            requests.get(uptime_kuma_url)
        except:
            pass
        time.sleep(60)
