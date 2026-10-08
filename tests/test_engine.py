from datetime import datetime, timedelta, timezone
from custom_components.neerslagkompas.models import RainPoint, SourceData
from custom_components.neerslagkompas.engine import assess

NOW = datetime(2026, 10, 8, 13, 15, tzinfo=timezone.utc)


def source(name, delay, rate):
    return SourceData(name, "nowcast", NOW, (
        RainPoint(NOW + timedelta(minutes=delay), rate),
    ))


def test_one_source_is_possible():
    prediction = assess({
        "buienradar": source("buienradar", 5, 4),
        "buienalarm": source("buienalarm", 5, 0),
    }, NOW)
    assert prediction.state == "Mogelijk regen"
    assert prediction.rain_within_30m is True


def test_two_sources_agree():
    prediction = assess({
        "buienradar": source("buienradar", 5, 3),
        "buienalarm": source("buienalarm", 10, 0.4),
    }, NOW)
    assert prediction.state == "Regen verwacht"
    assert len(prediction.agreeing_sources) == 2


def test_no_sources_means_no_data():
    assert assess({}, NOW).state == "Geen gegevens"
    assert assess({}, NOW).rain_within_30m is None


def test_stale_is_ignored():
    stale = SourceData(
        "buienradar", "nowcast", NOW - timedelta(hours=1),
        (RainPoint(NOW + timedelta(minutes=5), 3),)
    )
    assert assess({"buienradar": stale}, NOW).state == "Geen gegevens"


def test_hourly_cannot_vote_in_nowcast():
    hourly = SourceData("weerlive", "hourly", NOW,
        hourly=(RainPoint(NOW + timedelta(hours=1), 10, 60),))
    assert assess({"weerlive": hourly}, NOW).state == "Geen gegevens"
