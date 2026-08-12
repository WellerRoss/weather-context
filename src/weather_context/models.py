from datetime import datetime

from pydantic import BaseModel


class WeatherObservation(BaseModel):
    timestamp: datetime
    lat: float
    lon: float
    temp_c: float
    dewpoint_c: float | None
    humidity_pct: float | None
    heat_index_c: float | None
    wind_speed_ms: float | None
    precip_mm: float | None
    is_forecast: bool
