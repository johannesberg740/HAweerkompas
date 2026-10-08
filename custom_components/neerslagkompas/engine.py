"""Conservative nowcast fusion without confusing forecast and observation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import SourceData, is_fresh

THRESHOLD_MM_H = 0.1


@dataclass(frozen=True)
class RainAssessment:
    state: str
    start: datetime | None
    max_intensity_mm_h: float | None
    agreeing_sources: tuple[str, ...]
    used_sources: tuple[str, ...]
    rain_within_30m: bool | None


def assess(sources: dict[str, SourceData | None], now: datetime) -> RainAssessment:
    valid = {
        name: source
        for name, source in sources.items()
        if source and source.kind == "nowcast" and is_fresh(source, now)
    }
    if not valid:
        return RainAssessment("Geen gegevens", None, None, (), (), None)

    first_rain = {}
    maxima = []
    soon = False
    for name, source in valid.items():
        horizon = [
            point for point in source.points
            if now - timedelta(minutes=5) <= point.at <= now + timedelta(hours=2)
        ]
        rain = [point for point in horizon if point.intensity_mm_h >= THRESHOLD_MM_H]
        if rain:
            first_rain[name] = rain[0].at
            maxima.append(max(point.intensity_mm_h for point in rain))
            soon |= any(point.at <= now + timedelta(minutes=30) for point in rain)

    if not first_rain:
        return RainAssessment("Geen regen voorspeld", None, 0.0, (), tuple(valid), False)

    groups = [
        tuple(
            name for name, timestamp in first_rain.items()
            if abs(timestamp - start) <= timedelta(minutes=10)
        )
        for start in first_rain.values()
    ]
    consensus = max(groups, key=len)
    confirmed = len(consensus) >= 2
    return RainAssessment(
        "Regen verwacht" if confirmed else "Mogelijk regen",
        min(first_rain.values()),
        max(maxima),
        consensus if confirmed else (),
        tuple(valid),
        soon,
    )
