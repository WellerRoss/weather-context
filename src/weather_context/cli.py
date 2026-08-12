from datetime import datetime

import typer

from weather_context.client import forecast as fetch_forecast
from weather_context.client import historical as fetch_historical
from weather_context.models import WeatherObservation

app = typer.Typer(help="Look up historical or forecast weather for a lat/lon and time.")


def _print(label: str, obs: WeatherObservation) -> None:
    typer.echo(f"{label} for ({obs.lat}, {obs.lon}) at {obs.timestamp.isoformat()}")
    typer.echo(
        f"  temp: {obs.temp_c}C  feels-like: {obs.heat_index_c}C  humidity: {obs.humidity_pct}%"
    )
    typer.echo(
        f"  dewpoint: {obs.dewpoint_c}C  wind: {obs.wind_speed_ms} m/s  precip: {obs.precip_mm} mm"
    )


@app.command()
def historical(
    lat: float = typer.Option(..., help="Latitude."),
    lon: float = typer.Option(..., help="Longitude."),
    at: str = typer.Option(..., help="ISO 8601 timestamp, e.g. 2026-08-01T07:30:00."),
) -> None:
    """Look up historical weather conditions at a place/time."""
    obs = fetch_historical(lat, lon, datetime.fromisoformat(at))
    _print("Historical", obs)


@app.command()
def forecast(
    lat: float = typer.Option(..., help="Latitude."),
    lon: float = typer.Option(..., help="Longitude."),
    at: str = typer.Option(..., help="ISO 8601 timestamp, e.g. 2026-08-13T07:30:00."),
) -> None:
    """Look up forecast weather conditions at a place/time."""
    obs = fetch_forecast(lat, lon, datetime.fromisoformat(at))
    _print("Forecast", obs)


if __name__ == "__main__":
    app()
