from datetime import UTC, datetime
from typing import Any

import httpx

from weather_context.cache import Cache, to_hour
from weather_context.config import Settings, get_settings
from weather_context.models import WeatherObservation

_HOURLY_FIELDS = (
    "temperature_2m,dewpoint_2m,relative_humidity_2m,apparent_temperature,"
    "wind_speed_10m,precipitation"
)
_HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _parse_hourly(
    data: dict[str, Any], lat: float, lon: float, is_forecast: bool
) -> list[WeatherObservation]:
    hourly = data["hourly"]
    observations = []
    for i, time_str in enumerate(hourly["time"]):

        def value(field: str, i: int = i) -> float | None:
            v = hourly.get(field, [None] * len(hourly["time"]))[i]
            return None if v is None else float(v)

        temp_c = value("temperature_2m")
        if temp_c is None:
            continue
        observations.append(
            WeatherObservation(
                timestamp=datetime.fromisoformat(time_str).replace(tzinfo=UTC),
                lat=lat,
                lon=lon,
                temp_c=temp_c,
                dewpoint_c=value("dewpoint_2m"),
                humidity_pct=value("relative_humidity_2m"),
                # Open-Meteo doesn't expose a dedicated heat-index field; apparent
                # temperature (feels-like, combining humidity + wind) is the closest
                # available proxy.
                heat_index_c=value("apparent_temperature"),
                wind_speed_ms=value("wind_speed_10m"),
                precip_mm=value("precipitation"),
                is_forecast=is_forecast,
            )
        )
    return observations


def historical(
    lat: float,
    lon: float,
    timestamp: datetime,
    *,
    use_cache: bool = True,
    settings: Settings | None = None,
) -> WeatherObservation:
    """Historical conditions at a place/hour. Cached locally — past weather never
    changes, so a cache hit is returned as-is without a network call.

    `settings` lets an embedding application (e.g. a sibling repo importing this one
    as a library) pin the cache location explicitly instead of relying on this
    process's cwd-relative .env/DATA_DIR — important when multiple repos with their
    own same-named DATA_DIR setting are combined in one process, where env-based
    auto-discovery would silently resolve to the wrong directory instead of erroring.
    Defaults to get_settings() (the standalone-CLI behavior) when omitted."""
    settings = settings or get_settings()
    settings.ensure_dirs()
    cache = Cache(settings.cache_db_path) if use_cache else None
    try:
        if cache is not None:
            cached = cache.get(lat, lon, timestamp)
            if cached is not None:
                return cached

        day = to_hour(timestamp).date()
        response = httpx.get(
            _HISTORICAL_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": day.isoformat(),
                "end_date": day.isoformat(),
                "hourly": _HOURLY_FIELDS,
                "wind_speed_unit": "ms",
                "timezone": "UTC",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        observations = _parse_hourly(response.json(), lat, lon, is_forecast=False)

        if cache is not None:
            cache.put_many(lat, lon, observations)

        target = to_hour(timestamp)
        for obs in observations:
            if obs.timestamp == target:
                return obs
        raise ValueError(
            f"Open-Meteo returned no observation for {target.isoformat()} at ({lat}, {lon})"
        )
    finally:
        if cache is not None:
            cache.close()


def forecast(lat: float, lon: float, timestamp: datetime) -> WeatherObservation:
    """Forecast conditions at a place/hour. Always fetched live — never cached,
    since a forecast for a given hour changes as the date approaches."""
    target = to_hour(timestamp)
    response = httpx.get(
        _FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": target.date().isoformat(),
            "end_date": target.date().isoformat(),
            "hourly": _HOURLY_FIELDS,
            "wind_speed_unit": "ms",
            "timezone": "UTC",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    observations = _parse_hourly(response.json(), lat, lon, is_forecast=True)

    for obs in observations:
        if obs.timestamp == target:
            return obs
    raise ValueError(f"Open-Meteo returned no forecast for {target.isoformat()} at ({lat}, {lon})")
