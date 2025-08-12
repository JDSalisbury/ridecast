# fetchers/openweather.py
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Tuple
from fetchers.base import WeatherFetcher
from config import OPENWEATHER_API_KEY
from models import ForecastResult
from logger import logger
from api_utils import retry_with_backoff, find_forecast_with_fallback
from weather_config import default_config

LOCAL_TZ = ZoneInfo("America/New_York")


class OpenWeather(WeatherFetcher):
    source = "openweather"
    API_KEY = OPENWEATHER_API_KEY
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def get_forecast(self, lat: float, lon: float, hour_range: Tuple[int, int] = (8, 9)) -> ForecastResult | None:
        if "openweather" not in default_config.enabled_apis:
            logger.info("OpenWeather API disabled in configuration")
            return None
            
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.API_KEY,
            "units": "metric"
        }

        # API call with retry logic
        def make_request():
            return requests.get(
                self.BASE_URL, 
                params=params, 
                timeout=default_config.api_timeout_seconds
            )

        response = retry_with_backoff(
            make_request,
            default_config,
            f"OpenWeather API call for {lat}, {lon}"
        )
        
        if not response:
            return None

        try:
            data = response.json()
            forecasts = data.get("list", [])
            
            if not forecasts:
                logger.warning(f"OpenWeather: No forecasts returned for {lat}, {lon}")
                return None

            now = datetime.now(LOCAL_TZ)

            # Helper function to extract datetime from forecast
            def extract_time(forecast):
                dt_utc = datetime.strptime(
                    forecast["dt_txt"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                return dt_utc.astimezone(LOCAL_TZ)

            # Find forecast with fallback logic
            selected_forecast, used_fallback, offset_hours = find_forecast_with_fallback(
                forecasts, hour_range, now, default_config, extract_time
            )

            if not selected_forecast:
                logger.warning(
                    f"OpenWeather: No suitable forecast found for {lat}, {lon} in range {hour_range} "
                    f"(checked {len(forecasts)} forecasts, fallback enabled: {default_config.enable_fallback})"
                )
                return None

            # Log fallback usage
            forecast_time = extract_time(selected_forecast)
            if used_fallback:
                logger.info(f"OpenWeather: Using fallback forecast for {lat}, {lon} - "
                           f"target range {hour_range}, found {forecast_time.hour}:00 "
                           f"(offset: {offset_hours:+d}h)")

            # Create result
            rain = selected_forecast.get("rain", {}).get("3h", 0.0) > 0
            return ForecastResult(
                rain=rain,
                chance_of_rain=selected_forecast.get("pop", 0.0) * 100,
                precip_mm=selected_forecast.get("rain", {}).get("3h", 0.0),
                wind_kph=selected_forecast["wind"]["speed"] * 3.6,
                temp_c=selected_forecast["main"]["temp"],
                source="openweather",
                forecast_datetime=forecast_time,
                used_fallback=used_fallback,
                fallback_offset_hours=offset_hours
            )

        except Exception as e:
            logger.error(f"OpenWeather: Error parsing response for {lat}, {lon}: {e}")
            return None
