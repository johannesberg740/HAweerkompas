"""Bounded, fresh per-provider forecast series for Home Assistant dashboards.

No synthetic zeros: missing timestamps are left absent and invalid sources have
no published forecast points.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .models import SourceData, is_fresh

FORECAST_HORIZON = timedelta(hours=2)
MAX_FORECAST_POINTS = 30


def forecast_points(data: SourceData | None, now: datetime) -> list[dict[str, str | float]]:
    """Return timestamps in UTC and precipitation rate in millimetres/hour."""
    if not data or data.kind != "nowcast" or not is_fresh(data, now):
        return []

    points = sorted(
        (
            point for point in data.points
            if now - timedelta(minutes=5) <= point.at <= now + FORECAST_HORIZON
        ),
        key=lambda point: point.at,
    )
    return [
        {
            "datetime": point.at.isoformat(),
            "intensity_mm_h": round(point.intensity_mm_h, 3),
        }
        for point in points[:MAX_FORECAST_POINTS]
    ]
