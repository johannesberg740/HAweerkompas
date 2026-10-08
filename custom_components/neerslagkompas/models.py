"""Normalized rain observations and forecasts (UTC-aware timestamps)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

Kind = Literal["nowcast", "hourly", "observation"]


@dataclass(frozen=True, slots=True)
class RainPoint:
    at: datetime
    intensity_mm_h: float
    interval_minutes: int = 5

    def __post_init__(self):
        if self.at.tzinfo is None or self.at.utcoffset() is None:
            raise ValueError("RainPoint timestamp must be timezone-aware")
        if not 0 <= self.intensity_mm_h <= 1000:
            raise ValueError("Invalid precipitation intensity")
        if self.interval_minutes < 1:
            raise ValueError("Invalid interval")


@dataclass(frozen=True, slots=True)
class SourceData:
    source: str
    kind: Kind
    received_at: datetime
    points: tuple[RainPoint, ...] = ()
    description: str | None = None
    hourly: tuple[RainPoint, ...] = ()
    daily: tuple[dict, ...] = ()
    observed_at: datetime | None = None
    attribution: str = ""


FRESHNESS = {
    "buienradar": timedelta(minutes=20),
    "buienalarm": timedelta(minutes=20),
    "knmi_radar": timedelta(minutes=40),
    "weerlive": timedelta(hours=2),
}


def is_fresh(data: SourceData | None, now: datetime) -> bool:
    return bool(
        data is not None
        and timedelta(0) <= now - data.received_at <= FRESHNESS.get(
            data.source, timedelta(minutes=20)
        )
    )
