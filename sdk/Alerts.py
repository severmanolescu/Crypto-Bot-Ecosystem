from sdk.SendTelegramMessage import TelegramMessagesHandler
from sdk import LoadVariables as LoadVariables

from sdk.Logger import setup_logger
logger = setup_logger("log.log")
logger.info("Alerts scrtipt started")

def format_change(change):
    if change is None:
        return "N/A"
    if change < 0:
        return f"`🔴 {change:.2f}%`"  # Negative change in monospace
    else:
        return f"`🟢 +{change:.2f}%`"  # Positive change in monospace

class AlertsHandler:
    def __init__(self):
        self.alert_threshold_1h = None
        self.alert_threshold_24h = None
        self.alert_threshold_7d = None
        self.alert_threshold_30d = None

        self.telegram_api_token_alerts = None

        self.telegram_message = TelegramMessagesHandler()

        self.reload_the_data()

    def reload_the_data(self):
        variables = LoadVariables.load()

        self.telegram_api_token_alerts = variables.get("TELEGRAM_API_TOKEN_ALERTS", "")

        self.alert_threshold_1h = LoadVariables.get_int_variable("ALERT_THRESHOLD_1h", 2.5)
        self.alert_threshold_24h = LoadVariables.get_int_variable("ALERT_THRESHOLD_24h", 5)
        self.alert_threshold_7d = LoadVariables.get_int_variable("ALERT_THRESHOLD_7d", 10)
        self.alert_threshold_30d = LoadVariables.get_int_variable("ALERT_THRESHOLD_30d", 10)

        self.telegram_message.reload_the_data()

    # Check for alerts every 30 minutes
    async def check_for_major_updates_1h(self, now_date, top_100_crypto, update = None):
        alert_message = "🚨 *Crypto Alert!* Significant 1-hour change detected:\n\n"
        alerts_found = False

        for symbol, data in top_100_crypto.items():
            change_1h = data["change_1h"]

            if abs(change_1h) >= self.alert_threshold_1h:
                alerts_found = True
                alert_message += f"*{symbol}* → {format_change(change_1h)}\n"

        if alerts_found:
            await self.telegram_message.send_telegram_message(alert_message, self.telegram_api_token_alerts,
                                                              False, update)

            return True
        else:
            logger.error(f" No major price movement!")
            print(f"No major 1h price movement at {now_date.strftime('%H:%M')}")

        return False

    async def check_for_major_updates_24h(self, now_date, top_100_crypto, update = None):
        alert_message = "🚨 *Crypto Alert!* Significant 24-hours change detected:\n\n"
        alerts_found = False

        for symbol, data in top_100_crypto.items():
            change_24h = data["change_24h"]

            if abs(change_24h) >= self.alert_threshold_24h:
                alerts_found = True
                alert_message += f"*{symbol}* → {format_change(change_24h)}\n"

        if alerts_found:
            await self.telegram_message.send_telegram_message(alert_message, self.telegram_api_token_alerts,
                                                              False, update)

            return True
        else:
            logger.error(f" No major price movement!")
            print(f"No major 24h price movement at {now_date.strftime('%H:%M')}")

        return False

    async def check_for_major_updates_7d(self, now_date, top_100_crypto, update = None):
        alert_message = "🚨 *Crypto Alert!* Significant 7-days change detected:\n\n"
        alerts_found = False

        for symbol, data in top_100_crypto.items():
            change_7d = data["change_7d"]

            if abs(change_7d) >= self.alert_threshold_7d:
                alerts_found = True
                alert_message += f"*{symbol}* → {format_change(change_7d)}\n"

        if alerts_found:
            await self.telegram_message.send_telegram_message(alert_message, self.telegram_api_token_alerts,
                                                              False, update)

            return True
        else:
            logger.error(f" No major price movement!")
            print(f"No major 7d price movement at {now_date.strftime('%H:%M')}")

        return False

    async def check_for_major_updates_30d(self, now_date, top_100_crypto, update = None):
        alert_message = "🚨 *Crypto Alert!* Significant 30-days change detected:\n\n"
        alerts_found = False

        for symbol, data in top_100_crypto.items():
            change_30d = data["change_30d"]

            if abs(change_30d) >= self.alert_threshold_30d:
                alerts_found = True
                alert_message += f"*{symbol}* → {format_change(change_30d)}\n"

        if alerts_found:
            await self.telegram_message.send_telegram_message(alert_message, self.telegram_api_token_alerts,
                                                              False, update)

            return True
        else:
            logger.error(f" No major price movement!")
            print(f"No major 30d price movement at {now_date.strftime('%H:%M')}")

        return False

    async def check_for_alerts(self, now_date, top_100_crypto, update = None):
        await self.check_for_major_updates_1h(now_date, top_100_crypto, update)
        await self.check_for_major_updates_24h(now_date, top_100_crypto, update)
        await self.check_for_major_updates_7d(now_date, top_100_crypto, update)
        await self.check_for_major_updates_30d(now_date, top_100_crypto, update)