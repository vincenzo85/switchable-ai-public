"""Orologio e generatore di id reali."""
from __future__ import annotations

import time
import uuid

from core.ports import ClockPort, IdGeneratorPort


class SystemClock(ClockPort):
    def now(self):
        return time.time()


class FlightIds(IdGeneratorPort):
    def new_id(self):
        return f"flight-{uuid.uuid4().hex[:10]}"
