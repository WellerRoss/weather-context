import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from weather_context.models import WeatherObservation

# Historical weather at a given place/hour never changes, so bucketing lat/lon to
# ~1.1km keeps the cache small without meaningfully changing which data you get back
# (well within Open-Meteo's underlying reanalysis grid resolution).
_COORD_PRECISION = 2


def _bucket(value: float) -> float:
    return round(value, _COORD_PRECISION)


def to_hour(timestamp: datetime) -> datetime:
    ts = timestamp.astimezone(UTC) if timestamp.tzinfo else timestamp.replace(tzinfo=UTC)
    return ts.replace(minute=0, second=0, microsecond=0)


class Cache:
    """Local cache of *historical* observations only.

    Forecasts are never cached here — a forecast for a given hour changes as the
    date approaches, so caching it would go stale in a way that's actively
    misleading. See client.forecast().
    """

    def __init__(self, db_path: Path) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historical_observations (
                lat_bucket REAL NOT NULL,
                lon_bucket REAL NOT NULL,
                timestamp_utc TEXT NOT NULL,
                temp_c REAL NOT NULL,
                dewpoint_c REAL,
                humidity_pct REAL,
                heat_index_c REAL,
                wind_speed_ms REAL,
                precip_mm REAL,
                PRIMARY KEY (lat_bucket, lon_bucket, timestamp_utc)
            )
            """
        )
        self._conn.commit()

    def get(self, lat: float, lon: float, timestamp: datetime) -> WeatherObservation | None:
        row = self._conn.execute(
            """
            SELECT timestamp_utc, temp_c, dewpoint_c, humidity_pct, heat_index_c,
                   wind_speed_ms, precip_mm
            FROM historical_observations
            WHERE lat_bucket = ? AND lon_bucket = ? AND timestamp_utc = ?
            """,
            (_bucket(lat), _bucket(lon), to_hour(timestamp).isoformat()),
        ).fetchone()
        if row is None:
            return None
        return WeatherObservation(
            timestamp=datetime.fromisoformat(row[0]),
            lat=lat,
            lon=lon,
            temp_c=row[1],
            dewpoint_c=row[2],
            humidity_pct=row[3],
            heat_index_c=row[4],
            wind_speed_ms=row[5],
            precip_mm=row[6],
            is_forecast=False,
        )

    def put_many(self, lat: float, lon: float, observations: list[WeatherObservation]) -> None:
        self._conn.executemany(
            """
            INSERT OR REPLACE INTO historical_observations
                (lat_bucket, lon_bucket, timestamp_utc, temp_c, dewpoint_c, humidity_pct,
                 heat_index_c, wind_speed_ms, precip_mm)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    _bucket(lat),
                    _bucket(lon),
                    to_hour(obs.timestamp).isoformat(),
                    obs.temp_c,
                    obs.dewpoint_c,
                    obs.humidity_pct,
                    obs.heat_index_c,
                    obs.wind_speed_ms,
                    obs.precip_mm,
                )
                for obs in observations
            ],
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
