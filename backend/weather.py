"""
Smart Farming Assistant — Weather Service Subsystem (SIH 26180)
Provides real-time and forecast weather telemetry for localized farm conditions.

Design principles:
- Fully decoupled: Weather integration does not alter existing sensor or vision contracts.
- Configurable via environment variables: WEATHER_API_KEY, WEATHER_LAT, WEATHER_LON, WEATHER_LOCATION.
- Optional & graceful: If WEATHER_API_KEY is not configured or external calls fail/timeout,
  the service degrades cleanly and returns None without raising unhandled exceptions.
- Testable: Supports mock injection and uses standard httpx clients with strict timeouts.
"""

import sys

if __name__ == "backend.weather":
    sys.modules.setdefault("weather", sys.modules[__name__])
elif __name__ == "weather":
    sys.modules.setdefault("backend.weather", sys.modules[__name__])
    try:
        import backend
        setattr(backend, "weather", sys.modules[__name__])
    except ImportError:
        pass

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx


try:
    from backend.schemas import WeatherData, WeatherForecastItem
except ImportError:
    from schemas import WeatherData, WeatherForecastItem


logger = logging.getLogger("smart_farming.weather")

# Default geographic coordinates & configuration
DEFAULT_LAT: float = 28.6139
DEFAULT_LON: float = 77.2090
DEFAULT_LOCATION: str = "New Delhi, IN"
DEFAULT_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
DEFAULT_TIMEOUT_SECONDS: float = 3.0


def get_weather_config() -> Dict[str, Any]:
    """Retrieves weather configuration from environment variables."""
    api_key = os.environ.get("WEATHER_API_KEY")
    try:
        lat = float(os.environ.get("WEATHER_LAT", DEFAULT_LAT))
    except (ValueError, TypeError):
        lat = DEFAULT_LAT

    try:
        lon = float(os.environ.get("WEATHER_LON", DEFAULT_LON))
    except (ValueError, TypeError):
        lon = DEFAULT_LON

    location = os.environ.get("WEATHER_LOCATION", DEFAULT_LOCATION)
    base_url = os.environ.get("WEATHER_API_BASE_URL", DEFAULT_BASE_URL)

    return {
        "api_key": api_key,
        "lat": lat,
        "lon": lon,
        "location": location,
        "base_url": base_url,
    }


def parse_weather_response(
    current_data: Dict[str, Any],
    forecast_data: Optional[Dict[str, Any]] = None,
    location_name: Optional[str] = None,
) -> WeatherData:
    """
    Parses OpenWeatherMap-compliant response structures into a standardized WeatherData model.
    """
    # Current conditions
    main_section = current_data.get("main", {})
    weather_list = current_data.get("weather", [{}])
    weather_desc = weather_list[0].get("main", "Clear") if weather_list else "Clear"

    temp = float(main_section.get("temp", 25.0))
    humidity = float(main_section.get("humidity", 50.0))

    wind_section = current_data.get("wind", {})
    wind_speed_ms = wind_section.get("speed")
    wind_speed_kmh = round(wind_speed_ms * 3.6, 1) if wind_speed_ms is not None else None

    # Rain probability / current rain indicators
    rain_section = current_data.get("rain", {})
    current_has_rain = bool(rain_section) or "rain" in weather_desc.lower()
    rain_probability = 80.0 if current_has_rain else 10.0

    # Parse forecast periods if present
    forecast_items: List[WeatherForecastItem] = []
    is_rain_forecasted = current_has_rain

    if forecast_data and "list" in forecast_data:
        # OpenWeatherMap 5-day / 3-hour forecast returns 40 items (every 3 hours)
        # Group or pick representative daily/upcoming time blocks
        seen_dates = set()
        for entry in forecast_data.get("list", []):
            dt_txt = entry.get("dt_txt", "")
            date_part = dt_txt.split(" ")[0] if " " in dt_txt else dt_txt[:10]

            if date_part and date_part not in seen_dates and len(forecast_items) < 3:
                seen_dates.add(date_part)
                f_main = entry.get("main", {})
                f_weather = entry.get("weather", [{}])[0]
                f_pop = float(entry.get("pop", 0.0)) * 100.0  # Probability of precipitation (0.0 - 1.0)
                f_cond = f_weather.get("main", "Clear")

                if f_pop >= 50.0 or "rain" in f_cond.lower():
                    is_rain_forecasted = True

                forecast_items.append(
                    WeatherForecastItem(
                        time=date_part,
                        temp_max=round(float(f_main.get("temp_max", f_main.get("temp", 25.0))), 1),
                        temp_min=round(float(f_main.get("temp_min", f_main.get("temp", 20.0))), 1),
                        condition=f_cond,
                        rain_probability=round(f_pop, 1),
                    )
                )

    resolved_location = location_name or current_data.get("name") or DEFAULT_LOCATION

    return WeatherData(
        location=resolved_location,
        temperature=round(temp, 1),
        humidity=round(humidity, 1),
        condition=weather_desc,
        rain_probability=round(rain_probability, 1),
        wind_speed_kmh=wind_speed_kmh,
        is_rain_forecasted=is_rain_forecasted,
        forecast=forecast_items,
        source="OpenWeatherMap",
        timestamp=datetime.now(timezone.utc),
    )


async def fetch_weather_async(
    client: Optional[httpx.AsyncClient] = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Optional[WeatherData]:
    """
    Asynchronously fetches current weather and forecast from configured weather API.
    Gracefully returns None if API key is missing, network fails, or timeout occurs.
    """
    config = get_weather_config()
    api_key = config["api_key"]

    if not api_key:
        logger.debug("WEATHER_API_KEY is not configured; skipping weather fetch.")
        return None

    lat = config["lat"]
    lon = config["lon"]
    base_url = config["base_url"]
    location_name = config["location"]

    weather_url = f"{base_url}/weather"
    forecast_url = f"{base_url}/forecast"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}

    # Use provided client or instantiate a temporary one
    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=timeout)
        should_close = True

    try:
        # 1. Fetch current weather
        resp_current = await client.get(weather_url, params=params)
        if resp_current.status_code != 200:
            logger.warning(
                "Weather API returned status %d for current weather: %s",
                resp_current.status_code,
                resp_current.text,
            )
            return None

        current_data = resp_current.json()

        # 2. Fetch forecast (optional; failure does not invalidate current weather)
        forecast_data = None
        try:
            resp_forecast = await client.get(forecast_url, params=params)
            if resp_forecast.status_code == 200:
                forecast_data = resp_forecast.json()
        except Exception as forecast_exc:
            logger.debug("Forecast fetch failed (continuing with current weather): %s", forecast_exc)

        return parse_weather_response(
            current_data=current_data,
            forecast_data=forecast_data,
            location_name=location_name,
        )

    except httpx.TimeoutException:
        logger.warning("Weather API request timed out after %.1f seconds.", timeout)
        return None
    except Exception as exc:
        logger.warning("Failed to fetch weather telemetry: %s", exc)
        return None
    finally:
        if should_close:
            await client.aclose()


def fetch_weather_sync(timeout: float = DEFAULT_TIMEOUT_SECONDS) -> Optional[WeatherData]:
    """
    Synchronous fallback for fetching weather data.
    Gracefully returns None if API key is missing or network fails.
    """
    config = get_weather_config()
    api_key = config["api_key"]

    if not api_key:
        return None

    lat = config["lat"]
    lon = config["lon"]
    base_url = config["base_url"]
    location_name = config["location"]

    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}

    try:
        with httpx.Client(timeout=timeout) as client:
            resp_current = client.get(f"{base_url}/weather", params=params)
            if resp_current.status_code != 200:
                return None
            current_data = resp_current.json()

            forecast_data = None
            try:
                resp_forecast = client.get(f"{base_url}/forecast", params=params)
                if resp_forecast.status_code == 200:
                    forecast_data = resp_forecast.json()
            except Exception:
                pass

            return parse_weather_response(
                current_data=current_data,
                forecast_data=forecast_data,
                location_name=location_name,
            )
    except Exception as exc:
        logger.warning("Sync weather fetch failed: %s", exc)
        return None
