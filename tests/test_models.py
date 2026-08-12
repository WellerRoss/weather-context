from datetime import UTC, datetime

from weather_context.models import WeatherObservation


def test_observation_accepts_missing_optional_fields():
    obs = WeatherObservation(
        timestamp=datetime(2026, 8, 1, 7, tzinfo=UTC),
        lat=40.0,
        lon=-105.0,
        temp_c=24.1,
        dewpoint_c=None,
        humidity_pct=None,
        heat_index_c=None,
        wind_speed_ms=None,
        precip_mm=None,
        is_forecast=False,
    )
    assert obs.temp_c == 24.1
    assert obs.dewpoint_c is None
