# std
import http.client
import logging
import urllib.parse
from typing import List

# project
from . import Notifier, Event, EventType, EventPriority


class TelegramNotifier(Notifier):
    def __init__(self, title_prefix: str, config: dict):
        logging.info("Initializing Telegram notifier.")
        super().__init__(title_prefix, config)
        try:
            self.token = config["bot_token"]
            self.chat_id = config["chat_id"]
        except KeyError as key:
            logging.error(f"Invalid config.yaml. Missing key: {key}")

    def send_events_to_user(self, events: List[Event]) -> bool:
        errors = False
        for event in events:
            if event.type == EventType.USER:
                symbol = "\U0001F6A8" if event.priority == EventPriority.HIGH else ""
                conn = http.client.HTTPSConnection("api.telegram.org:443")
                conn.request(
                    "POST",
                    f"/bot{self.token}/sendMessage",
                    urllib.parse.urlencode(
                        {
                            "chat_id": self.chat_id,
                            "parse_mode": "HTML",
                            "text": f"<b>{symbol} {self._title_prefix} {event.service.name}</b>\n{event.message}",
                            "disable_notification": event.priority == EventPriority.LOW,
                        }
                    ),
                    {"Content-type": "application/x-www-form-urlencoded"},
                )
                response = conn.getresponse()
                if response.getcode() != 200:
                    logging.warning(f"Problem sending event to user, code: {response.getcode()}")
                    errors = True
                conn.close()

        return errors
