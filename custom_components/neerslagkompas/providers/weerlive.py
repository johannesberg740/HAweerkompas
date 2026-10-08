"""KNMI-derived Weerlive forecasts using the upstream maintained API client.

Reuse the Weerlive client already used by golles/ha-knmi rather than
reimplementing the response transport, decoding, rate limits and error mapping.
Only translate typed upstream models into NeerslagKompas's stable data model.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite

from weerlive import Response, WeerliveApi

from ..models import RainPoint, SourceData


def parse(response: Response, received_at: datetime) -> SourceData:
    """Normalize typed Weerlive results; preserve hourly/nowcast distinction."""
    if not isinstance(response, Response):
        raise ValueError("Unexpected Weerlive response type")

    hourly = []
    for forecast in response.hourly_forecast:
        precipitation = forecast.precipitation
        if not isfinite(precipitation) or precipitation < 0:
            continue
        hourly.append(
            RainPoint(
                datetime.fromtimestamp(forecast.timestamp, tz=timezone.utc),
                float(precipitation),
                interval_minutes=60,
            )
        )

    daily = tuple(
        {
            "date": forecast.day.date().isoformat()
            if forecast.day else None,
            "precipitation_probability_percent": (
                forecast.precipitation_probability
            ),
        }
        for forecast in response.daily_forecast
    )
    if not hourly and not daily and not response.live.forecast:
        raise ValueError("Weerlive returned no usable weather information")

    observed_at = datetime.fromtimestamp(
        response.live.timestamp, tz=timezone.utc
    )
    return SourceData(
        source="weerlive",
        kind="hourly",
        received_at=received_at,
        description=response.live.forecast,
        hourly=tuple(hourly),
        daily=daily,
        observed_at=observed_at,
        attribution="Weather data KNMI/NOAA via Weerlive.nl",
    )


class WeerliveClient:
    """Thin adapter around the upstream WeerliveApi library."""

    def __init__(self, session, key: str) -> None:
        self._client = WeerliveApi(key, session)

    async def async_fetch(
        self, latitude: float, longitude: float, now: datetime
    ) -> SourceData:
        response = await self._client.latitude_longitude(latitude, longitude)
        return parse(response, now)
