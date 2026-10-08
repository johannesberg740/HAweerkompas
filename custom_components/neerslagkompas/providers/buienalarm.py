"""Experimental Buienalarm/Infoplaza endpoint. Check terms before public release."""
from datetime import datetime, timezone, timedelta

from ..models import RainPoint, SourceData

URL = "https://imn-rust-lb.infoplaza.io/v4/nowcast/ba/timeseries/{lat}/{lon}/"


def parse(payload: dict, received_at: datetime) -> SourceData:
    series = payload.get("data")
    if not isinstance(series, list) or not series:
        raise ValueError("Missing Buienalarm timeseries")
    points = []
    previous = None
    for item in series:
        at = datetime.fromtimestamp(int(item["timestamp"]), tz=timezone.utc)
        if previous is not None and at <= previous:
            raise ValueError("Non-monotonic timestamps")
        previous = at
        points.append(RainPoint(at, float(item["precipitationrate"])))
    if abs(points[0].at - received_at) > timedelta(minutes=40):
        raise ValueError("Stale Buienalarm timeseries")
    return SourceData("buienalarm", "nowcast", received_at, tuple(points),
                      attribution="Buienalarm / Infoplaza")


class BuienalarmClient:
    def __init__(self, session):
        self.session = session

    async def async_fetch(self, latitude: float, longitude: float, now: datetime) -> SourceData:
        url = URL.format(lat=f"{latitude:.5f}", lon=f"{longitude:.5f}")
        async with self.session.get(url, timeout=12) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)
        return parse(payload, now)
