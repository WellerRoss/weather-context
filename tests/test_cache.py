from datetime import UTC, datetime

from weather_context.cache import Cache
from weather_context.models import WeatherObservation


def _obs(lat: float, lon: float, hour: int) -> WeatherObservation:
    return WeatherObservation(
        timestamp=datetime(2026, 8, 1, hour, tzinfo=UTC),
        lat=lat,
        lon=lon,
        temp_c=20.0 + hour,
        dewpoint_c=15.0,
        humidity_pct=70.0,
        heat_index_c=21.0,
        wind_speed_ms=2.0,
        precip_mm=0.0,
        is_forecast=False,
    )


def test_miss_then_hit_roundtrip(tmp_path):
    cache = Cache(tmp_path / "cache.db")
    lat, lon = 40.0150, -105.2705
    timestamp = datetime(2026, 8, 1, 7, tzinfo=UTC)

    assert cache.get(lat, lon, timestamp) is None

    cache.put_many(lat, lon, [_obs(lat, lon, 7)])
    hit = cache.get(lat, lon, timestamp)

    assert hit is not None
    assert hit.temp_c == 27.0
    cache.close()


def test_nearby_coordinates_share_a_bucket(tmp_path):
    cache = Cache(tmp_path / "cache.db")
    timestamp = datetime(2026, 8, 1, 7, tzinfo=UTC)
    cache.put_many(40.011, -105.271, [_obs(40.011, -105.271, 7)])

    # Both round to the same 2-decimal (40.01, -105.27) bucket, so this counts as a hit.
    hit = cache.get(40.014, -105.274, timestamp)

    assert hit is not None
    cache.close()


def test_minutes_within_the_hour_share_a_cache_entry(tmp_path):
    cache = Cache(tmp_path / "cache.db")
    lat, lon = 40.0, -105.0
    cache.put_many(lat, lon, [_obs(lat, lon, 7)])

    hit = cache.get(lat, lon, datetime(2026, 8, 1, 7, 45, tzinfo=UTC))

    assert hit is not None
    cache.close()
