# std
import os
import unittest

# project
from src.notifier import Event, EventType, EventPriority, EventService
from src.notifier.telegram_notifier import TelegramNotifier


class TestTelegramNotifier(unittest.TestCase):
    def setUp(self) -> None:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.assertIsNotNone(bot_token, "You must export TELEGRAM_BOT_TOKEN as env variable")
        self.assertIsNotNone(chat_id, "You must export TELEGRAM_CHAT_ID as env variable")
        self.notifier = TelegramNotifier(
            title_prefix="Test", config={"enable": True, "bot_token": bot_token, "chat_id": chat_id}
        )

    def testLowPrioriyNotifications(self):
        errors = self.notifier.send_events_to_user(
            events=[
                Event(
                    type=EventType.USER,
                    priority=EventPriority.LOW,
                    service=EventService.HARVESTER,
                    message="Low priority notification 1.",
                ),
                Event(
                    type=EventType.USER,
                    priority=EventPriority.LOW,
                    service=EventService.HARVESTER,
                    message="Low priority notification 2.",
                ),
            ]
        )
        self.assertFalse(errors)

    def testNormalPrioriyNotifications(self):
        errors = self.notifier.send_events_to_user(
            events=[
                Event(
                    type=EventType.USER,
                    priority=EventPriority.NORMAL,
                    service=EventService.HARVESTER,
                    message="Normal priority notification.",
                )
            ]
        )
        self.assertFalse(errors)

    def testHighPrioriyNotifications(self):
        errors = self.notifier.send_events_to_user(
            events=[
                Event(
                    type=EventType.USER,
                    priority=EventPriority.HIGH,
                    service=EventService.HARVESTER,
                    message="This is a high priority notification!",
                )
            ]
        )
        self.assertFalse(errors)
