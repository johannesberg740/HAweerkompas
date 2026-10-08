"""Buienradar five-minute text nowcast, never an actual rain measurement."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ..models import RainPoint, SourceData

TZ = ZoneInfo("Europe/Amsterdam")
URL = "https://gps.buienradar.nl/getrr.php"


def decode_code(code: int) -> float:
    if code == 0:
        return 0.0
    if not 1 <= code <= 255:
        raise ValueError("Invalid rain code")
    return 10 ** ((code - 109) / 32)


def parse(text: str, received_at: datetime) -> SourceData:
    now_local = received_at.astimezone(TZ)
    points = []
    previous = None
    for line in text.splitlines():
        if not line.strip():
            continue
        raw, hhmm = line.strip().split("|", 1)
        hour, minute = map(int, hhmm.split(":"))
        if not 0 <= hour < 24 or not 0 <= minute < 60:
            raise ValueError("Invalid timestamp")
        candidates = [
            now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
            + timedelta(days=offset)
            for offset in (-1, 0, 1)
        ]
        at = min(candidates, key=lambda dt: abs(dt - now_local)) if previous is None else min(
            (dt for dt in candidates if dt > previous), default=None
        )
        if at is None:
            raise ValueError("Non-monotonic forecast")
        previous = at
        points.append(RainPoint(at, decode_code(int(raw))))
    if not points or abs(points[0].at - received_at) > timedelta(minutes=40):
        raise ValueError("Empty or stale Buienradar nowcast")
    return SourceData("buienradar", "nowcast", received_at, tuple(points),
                      attribution="Buienradar.nl")


class BuienradarClient:
    def __init__(self, session):
        self.session = session

    async def async_fetch(self, latitude: float, longitude: float, now: datetime) -> SourceData:
        async with self.session.get(
            URL, params={"lat": latitude, "lon": longitude}, timeout=12
        ) as response:
            response.raise_for_status()
            return parse(await response.text(), now)
