import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import respx
from httpx import Response

from weather_context.client import forecast, historical
from weather_context.config import Settings

FIXTURE = json.loads(
    (Path(__file__).parent.parent / "fixtures" / "open_meteo_hourly_sample.json").read_text()
)
LAT, LON = 40.015, -105.2705
TARGET = datetime(2026, 8, 1, 7, tzinfo=UTC)


@respx.mock
def test_historical_parses_and_returns_matching_hour():
    route = respx.get("https://archive-api.open-meteo.com/v1/archive").mock(
        return_value=Response(200, json=FIXTURE)
    )

    obs = historical(LAT, LON, TARGET)

    assert route.called
    assert obs.temp_c == 24.1
    assert obs.heat_index_c == 26.8
    assert obs.is_forecast is False


@respx.mock
def test_historical_second_call_hits_cache_not_network():
    route = respx.get("https://archive-api.open-meteo.com/v1/archive").mock(
        return_value=Response(200, json=FIXTURE)
    )

    historical(LAT, LON, TARGET)
    historical(LAT, LON, TARGET)

    assert route.call_count == 1


@respx.mock
def test_forecast_always_hits_network():
    route = respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=Response(200, json=FIXTURE)
    )

    obs1 = forecast(LAT, LON, TARGET)
    obs2 = forecast(LAT, LON, TARGET)

    assert route.call_count == 2
    assert obs1.is_forecast is True
    assert obs2.is_forecast is True


@respx.mock
def test_historical_raises_when_hour_missing_from_response():
    respx.get("https://archive-api.open-meteo.com/v1/archive").mock(
        return_value=Response(200, json=FIXTURE)
    )

    with pytest.raises(ValueError, match="no observation"):
        historical(LAT, LON, datetime(2026, 8, 1, 23, tzinfo=UTC))


@respx.mock
def test_historical_respects_explicit_settings_override(tmp_path):
    respx.get("https://archive-api.open-meteo.com/v1/archive").mock(
        return_value=Response(200, json=FIXTURE)
    )
    explicit_dir = tmp_path / "explicit-weather-data"
    settings = Settings(data_dir=explicit_dir)

    historical(LAT, LON, TARGET, settings=settings)

    assert (explicit_dir / "cache.db").exists()
