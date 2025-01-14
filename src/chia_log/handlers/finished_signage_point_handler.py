# std
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

# project
from src.notifier import Event, EventService, EventType, EventPriority
from . import LogHandler
from ..parsers.finished_signage_point_parser import FinishedSignagePointParser, FinishedSignagePointMessage


class FinishedSignagePointHandler(LogHandler):
    """This handler parses all logs indicating finished signage point
    activity by the full node. It holds a list of condition checkers
    that are evaluated for each event.
    """

    def __init__(self):
        self._parser = FinishedSignagePointParser()
        self._cond_checkers: List[ConditionChecker] = [NonSkippedSignagePoints()]

    def handle(self, logs: str) -> List[Event]:
        """Process incoming logs, check all conditions
        and return a list of notable events.
        """

        events = []
        signage_point_messages = self._parser.parse(logs)
        if len(signage_point_messages) > 0:
            # Currently not generating keep-alive events for the full node
            # based on the signage points because it's tightly coupled to
            # the eligible plots check from the harvester
            logging.debug(f"Parsed {len(signage_point_messages)} signage point messages")

        # Run messages through all condition checkers
        for msg in signage_point_messages:
            for checker in self._cond_checkers:
                event = checker.check(msg)
                if event:
                    events.append(event)

        return events


class ConditionChecker(ABC):
    @abstractmethod
    def check(self, obj: FinishedSignagePointMessage) -> Optional[Event]:
        pass


class NonSkippedSignagePoints(ConditionChecker):
    """Check that the full node did not skip any signage points.
    If there are signage points missing, this could indicate connection
    issues which prevent the farmer from participating in all challenges.
    """

    def __init__(self):
        logging.info("Enabled check for finished signage points.")
        self._last_signage_point_timestamp = None
        self._last_signage_point = None
        self._roll_over_point = 64

    def check(self, obj: FinishedSignagePointMessage) -> Optional[Event]:
        if self._last_signage_point is None:
            self._last_signage_point_timestamp = obj.timestamp
            self._last_signage_point = obj.signage_point
            return None

        event = None
        time_diff_seconds = (obj.timestamp - self._last_signage_point_timestamp).seconds
        increment_diff = obj.signage_point - (self._last_signage_point % self._roll_over_point)

        if increment_diff <= 0 or increment_diff > 1:
            # This is hacky addition to prevent false alarms for some network-wide issues that
            # aren't necessarily related to the local node. See "testNetworkScramble" test case.
            # Signage points are expected approx every 8-10 seconds. If a point was skipped for real
            # then we expect the time difference to be at least 2*8 seconds. Otherwise it's flaky event.
            if time_diff_seconds < 15:
                logging.info(
                    f"Detected unusual network activity. Last signage point {self._last_signage_point}, "
                    f"current signage point {obj.signage_point}. Time difference: {time_diff_seconds} "
                    f"seconds. Seems unrelated to the local node. Ignoring..."
                )
            else:
                message = (
                    f"Experiencing networking issues? Skipped some signage points! "
                    f"Last {self._last_signage_point}/64, current {obj.signage_point}/64."
                )
                logging.warning(message)
                event = Event(
                    type=EventType.USER, priority=EventPriority.NORMAL, service=EventService.FULL_NODE, message=message
                )

        self._last_signage_point_timestamp = obj.timestamp
        self._last_signage_point = obj.signage_point
        return event
