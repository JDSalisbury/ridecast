# fetchers/tomorrowio.py
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Tuple
from fetchers.base import WeatherFetcher
from config import TOMORROW_API_KEY
from models import ForecastResult
from logger import logger
from api_utils import retry_with_backoff, find_forecast_with_fallback
from weather_config import default_config

LOCAL_TZ = ZoneInfo("America/New_York")


class TomorrowIO(WeatherFetcher):
    source = "tomorrowio"
    BASE_URL = "https://api.tomorrow.io/v4/weather/forecast"

    def get_forecast(self, lat: float, lon: float, hour_range: Tuple[int, int] = (8, 9)) -> ForecastResult | None:
        if "tomorrowio" not in default_config.enabled_apis:
            logger.info("TomorrowIO API disabled in configuration")
            return None
            
        params = {
            "location": f"{lat},{lon}",
            "apikey": TOMORROW_API_KEY,
            "timesteps": "1h",
            "units": "metric",
            "fields": "precipitationProbability,precipitationIntensity,temperature,windSpeed"
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
            f"TomorrowIO API call for {lat}, {lon}"
        )
        
        if not response:
            return None

        try:
            data = response.json()
            timelines = data.get("timelines", {}).get("hourly", [])
            
            if not timelines:
                logger.warning(f"TomorrowIO: No hourly timelines returned for {lat}, {lon}")
                return None

            now = datetime.now(LOCAL_TZ)

            # Helper function to extract datetime from forecast
            def extract_time(forecast):
                dt_utc = datetime.fromisoformat(
                    forecast["time"].replace("Z", "+00:00"))
                return dt_utc.astimezone(LOCAL_TZ)

            # Find forecast with fallback logic
            selected_forecast, used_fallback, offset_hours = find_forecast_with_fallback(
                timelines, hour_range, now, default_config, extract_time
            )

            if not selected_forecast:
                logger.warning(
                    f"TomorrowIO: No suitable forecast found for {lat}, {lon} in range {hour_range} "
                    f"(checked {len(timelines)} forecasts, fallback enabled: {default_config.enable_fallback})"
                )
                return None

            # Log fallback usage
            forecast_time = extract_time(selected_forecast)
            if used_fallback:
                logger.info(f"TomorrowIO: Using fallback forecast for {lat}, {lon} - "
                           f"target range {hour_range}, found {forecast_time.hour}:00 "
                           f"(offset: {offset_hours:+d}h)")

            # Create result
            values = selected_forecast.get("values", {})
            precip_prob = values.get("precipitationProbability", 0.0)
            precip_intensity = values.get("precipitationIntensity", 0.0)

            return ForecastResult(
                rain=precip_prob >= 30 or precip_intensity > 0.0,
                chance_of_rain=precip_prob,
                precip_mm=precip_intensity,
                wind_kph=values.get("windSpeed", 0.0),
                temp_c=values.get("temperature", 0.0),
                source="tomorrowio",
                forecast_datetime=forecast_time,
                used_fallback=used_fallback,
                fallback_offset_hours=offset_hours
            )

        except Exception as e:
            logger.error(f"TomorrowIO: Error parsing response for {lat}, {lon}: {e}")
            return None
