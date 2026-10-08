"""Forecast source parsing regression tests."""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import AsyncMock

from weerlive import Response

from custom_components.neerslagkompas.providers.buienradar import (
    decode_code, parse as parse_buienradar,
)
from custom_components.neerslagkompas.providers.buienalarm import (
    parse as parse_buienalarm,
)
from custom_components.neerslagkompas.providers.weerlive import (
    parse as parse_weerlive, WeerliveClient,
)

UTC = timezone.utc
FIXTURES = Path(__file__).resolve().parent / "fixtures"


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


def upstream_weerlive_response():
    """Parse a real-schema, reduced upstream library fixture."""
    payload = (FIXTURES / "weerlive-amsterdam-v2.json").read_text()
    return Response.from_json(payload)


def test_weerlive_hourly_data_is_not_nowcast():
    response = upstream_weerlive_response()
    received = datetime.fromtimestamp(response.live.timestamp, UTC)
    data = parse_weerlive(response, received)
    assert data.kind == "hourly"
    assert data.source == "weerlive"
    assert data.points == ()
    assert len(data.hourly) == 2
    assert data.hourly[0].interval_minutes == 60
    assert data.hourly[0].at.tzinfo is UTC
    assert data.description == "Geleidelijk afnemende buiigheid"
    assert data.daily[0]["precipitation_probability_percent"] == 50


def test_weerlive_client_reuses_official_library_contract():
    async def test_run():
        response = upstream_weerlive_response()
        now = datetime.fromtimestamp(response.live.timestamp, UTC)
        # The actual library is instantiated with the shared Home Assistant
        # session. Stub only the network call and assert typed normalization.
        client = WeerliveClient(session=object(), key="dummy-key")
        client._client.latitude_longitude = AsyncMock(return_value=response)
        result = await client.async_fetch(52.71, 5.73, now)
        client._client.latitude_longitude.assert_awaited_once_with(52.71, 5.73)
        assert result.observed_at == now
        assert result.kind == "hourly"

    asyncio.run(test_run())


def test_weerlive_rejects_untyped_response():
    now = datetime(2026, 10, 8, tzinfo=UTC)
    try:
        parse_weerlive({"uur_verw": []}, now)
    except ValueError as error:
        assert str(error) == "Unexpected Weerlive response type"
    else:
        raise AssertionError("Weerlive must validate typed results")
