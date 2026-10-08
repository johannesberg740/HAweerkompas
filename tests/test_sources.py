from datetime import datetime, timezone, timedelta
from custom_components.neerslagkompas.providers.buienradar import (
    decode_code, parse as parse_buienradar,
)
from custom_components.neerslagkompas.providers.buienalarm import parse as parse_buienalarm
from custom_components.neerslagkompas.providers.weerlive import parse as parse_weerlive

UTC = timezone.utc


def test_zero_and_one():
    assert decode_code(0) == 0.0
    assert decode_code(109) == 1.0


def test_midnight_rollover():
    now = datetime(2026, 10, 8, 21, 58, tzinfo=UTC)
    points = parse_buienradar("000|23:55\n109|00:00\n000|00:05", now)
    assert points.points[1].at == datetime(2026, 10, 8, 22, 0, tzinfo=UTC)


def test_buienalarm_rate():
    now = datetime(2026, 10, 8, 13, 15, tzinfo=UTC)
    forecast = parse_buienalarm({"data": [
        {"timestamp": int(now.timestamp()), "precipitationrate": 3.4},
        {"timestamp": int((now + timedelta(minutes=5)).timestamp()), "precipitationrate": 0},
    ]}, now)
    assert forecast.points[0].intensity_mm_h == 3.4


def test_weerlive_does_not_count_as_nowcast():
    now = datetime(2026, 10, 8, 13, 15, tzinfo=UTC)
    context = parse_weerlive({
        "liveweer": [{"verw": "Wisselvallig"}],
        "uurverwachting": [{
            "timestamp": int(now.timestamp()), "neersl": "0.4"
        }],
    }, now)
    assert context.kind == "hourly"
    assert context.hourly[0].interval_minutes == 60
