"""KNMI-derived weather through Weerlive v2: hourly and daily context."""
from __future__ import annotations
from datetime import datetime, timezone
from ..models import RainPoint, SourceData

URL = "https://weerlive.nl/api/weerlive_api_v2.php"


def parse(payload: dict, received_at: datetime) -> SourceData:
    if not isinstance(payload, dict):
        raise ValueError("Malformed Weerlive response")
    raw_hours = payload.get("uurverwachting") or []
    live = (payload.get("liveweer") or [{}])[0]
    hours = []
    for item in raw_hours:
        if item.get("timestamp") is None or item.get("neersl") is None:
            continue
        try:
            value = float(item["neersl"])
            if value < 0:
                continue
            hours.append(
                RainPoint(
                    datetime.fromtimestamp(int(item["timestamp"]), timezone.utc),
                    value, 60
                )
            )
        except (TypeError, ValueError, OverflowError):
            continue
    if not isinstance(live, dict) or not live and not hours:
        raise ValueError("No useful Weerlive response")
    return SourceData(
        "weerlive", "hourly", received_at, description=live.get("verw"),
        hourly=tuple(hours), daily=tuple(payload.get("dagverwachting") or []),
        attribution="KNMI via Weerlive.nl (https://weerlive.nl/delen.php)",
    )


class WeerliveClient:
    def __init__(self, session, key: str):
        self.session, self.key = session, key

    async def async_fetch(
        self, latitude: float, longitude: float, now: datetime
    ) -> SourceData:
        params = {
            "key": self.key,
            "locatie": f"{latitude:.6f},{longitude:.6f}",
        }
        async with self.session.get(
            URL, params=params, timeout=15
        ) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)
        return parse(payload, now)
