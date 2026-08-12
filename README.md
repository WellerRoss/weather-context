# weather-context

Generic historical/forecast weather lookup by latitude/longitude, backed by
[Open-Meteo](https://open-meteo.com/). No API key required.

This is a standalone, ecosystem-agnostic library: the core API takes plain
`lat`/`lon`/`timestamp` and returns a plain `WeatherObservation` — it has no
dependency on, or knowledge of, any other project. It's built as one piece of a larger
personal running/analytics ecosystem (see the architecture plan this belongs to), but
nothing here assumes that context: it's equally usable standalone or in an unrelated
future project.

## Why Open-Meteo

Chosen over Visual Crossing (which offers a free tier of 1000 records/day with
real station-observation data): query volume for this use case is trivially low
either way, so the quota isn't a real differentiator. Open-Meteo needs **no API key**
— nothing to store in `.env`, rotate, or accidentally leak from a public repo — and
its historical data (ERA5 reanalysis, modeled/interpolated) is more than precise
enough for "was it hot/humid on this run" context.

**Revisit this if** precision starts to matter — e.g. a workout-distance prediction
model shows heat-index sensitivity where the reanalysis grid's smoothing is plausibly
costing accuracy. At that point, swapping in Visual Crossing's station-based data for
the historical path would be the natural next step.

## Usage

```python
from datetime import datetime
from weather_context import historical, forecast

obs = historical(lat=40.015, lon=-105.2705, timestamp=datetime(2026, 8, 1, 7, 30))
print(obs.temp_c, obs.heat_index_c, obs.humidity_pct)

obs = forecast(lat=40.015, lon=-105.2705, timestamp=datetime(2026, 8, 13, 7, 30))
```

Or via the CLI:

```
wx historical --lat 40.015 --lon -105.2705 --at 2026-08-01T07:30:00
wx forecast --lat 40.015 --lon -105.2705 --at 2026-08-13T07:30:00
```

## Caching

Historical lookups are cached locally in SQLite under `DATA_DIR` (default
`~/data/weather-context/`, configurable via `.env`) — past weather never changes, so a
cache hit skips the network call entirely. Lat/lon is bucketed to 2 decimal places
(~1km) and timestamps to the hour, matching Open-Meteo's underlying data resolution.

Forecasts are **never** cached — a forecast for a given hour changes as the date
approaches, so caching it would silently go stale. Every `forecast()` call hits the
API live.

## Setup

```
uv sync
cp .env.example .env   # optional — everything has a sensible default
uv run pytest
```

No credentials needed. `DATA_DIR` in `.env` only controls where the local cache lives.

## Data notes

- Wind speed is requested in m/s directly from Open-Meteo (`wind_speed_unit=ms`), not
  converted after the fact.
- `heat_index_c` is actually Open-Meteo's "apparent temperature" (feels-like,
  combining humidity + wind) — there's no dedicated heat-index field in the API. Close
  enough for run-conditions context, but not a textbook heat-index formula.
