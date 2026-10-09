"""Forecast-series tests: freshness, source type, horizon and missing gaps."""
from datetime import datetime, timedelta, timezone

from custom_components.neerslagkompas.forecast_series import forecast_points
from custom_components.neerslagkompas.models import RainPoint, SourceData

NOW = datetime(2026, 10, 9, 18, 0, tzinfo=timezone.utc)


def _source(name="knmi_radar", kind="nowcast", received=NOW, points=()):
    return SourceData(name, kind, received, points)


def test_series_is_sorted_and_keeps_actual_zeros_and_gaps():
    points = (
        RainPoint(NOW + timedelta(minutes=15), 2.4),
        RainPoint(NOW + timedelta(minutes=5), 0.0),
        RainPoint(NOW + timedelta(minutes=90), 1.2),
    )
    result = forecast_points(_source(points=points), NOW)
    assert [item["intensity_mm_h"] for item in result] == [0.0, 2.4, 1.2]
    assert [item["datetime"] for item in result] == [
        (NOW + timedelta(minutes=i)).isoformat() for i in (5, 15, 90)
    ]


def test_stale_and_hourly_never_show_as_nowcast():
    points = (RainPoint(NOW + timedelta(minutes=5), 1.5),)
    assert forecast_points(_source(received=NOW - timedelta(hours=1), points=points), NOW) == []
    assert forecast_points(_source(kind="hourly", points=points), NOW) == []
    assert forecast_points(None, NOW) == []


def test_horizon_is_limited_and_no_false_zero_added():
    points = (
        RainPoint(NOW - timedelta(minutes=10), 6.0),
        RainPoint(NOW + timedelta(minutes=2), 2.0),
        RainPoint(NOW + timedelta(hours=3), 5.0),
    )
    result = forecast_points(_source(points=points), NOW)
    assert len(result) == 1
    assert result[0]["intensity_mm_h"] == 2.0


def test_large_provider_response_is_bounded():
    points = tuple(RainPoint(NOW + timedelta(minutes=i), 0.5) for i in range(121))
    result = forecast_points(_source(points=points), NOW)
    assert len(result) == 30
