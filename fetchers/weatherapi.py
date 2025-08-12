import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Tuple
from fetchers.base import WeatherFetcher
from config import WEATHER_API_KEY
from models import ForecastResult
from logger import logger
from api_utils import retry_with_backoff, find_forecast_with_fallback
from weather_config import default_config

LOCAL_TZ = ZoneInfo("America/New_York")


class WeatherAPI(WeatherFetcher):
    source = "weatherapi"
    BASE_URL = "https://api.weatherapi.com/v1/forecast.json"

    def get_forecast(self, lat: float, lon: float, hour_range: Tuple[int, int] = (8, 9)) -> ForecastResult | None:
        if "weatherapi" not in default_config.enabled_apis:
            logger.info("WeatherAPI disabled in configuration")
            return None
            
        params = {
            "key": WEATHER_API_KEY,
            "q": f"{lat},{lon}",
            "days": 2,  # Get 2 days to handle edge cases near midnight
            "aqi": "no",
            "alerts": "no"
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
            f"WeatherAPI call for {lat}, {lon}"
        )
        
        if not response:
            return None

        try:
            data = response.json()
            forecast_days = data.get("forecast", {}).get("forecastday", [])
            
            if not forecast_days:
                logger.warning(f"WeatherAPI: No forecast days returned for {lat}, {lon}")
                return None

            # Collect all hourly forecasts from all days
            all_hours = []
            for day in forecast_days:
                hours = day.get("hour", [])
                all_hours.extend(hours)
            
            if not all_hours:
                logger.warning(f"WeatherAPI: No hourly forecasts returned for {lat}, {lon}")
                return None

            now = datetime.now(LOCAL_TZ)

            # Helper function to extract datetime from forecast (FIXED: now uses LOCAL_TZ)
            def extract_time(hour_forecast):
                # WeatherAPI returns local time already, but we need to make it timezone-aware
                dt_naive = datetime.strptime(hour_forecast["time"], "%Y-%m-%d %H:%M")
                return dt_naive.replace(tzinfo=LOCAL_TZ)

            # Find forecast with fallback logic
            selected_forecast, used_fallback, offset_hours = find_forecast_with_fallback(
                all_hours, hour_range, now, default_config, extract_time
            )

            if not selected_forecast:
                logger.warning(
                    f"WeatherAPI: No suitable forecast found for {lat}, {lon} in range {hour_range} "
                    f"(checked {len(all_hours)} forecasts, fallback enabled: {default_config.enable_fallback})"
                )
                return None

            # Log fallback usage
            forecast_time = extract_time(selected_forecast)
            if used_fallback:
                logger.info(f"WeatherAPI: Using fallback forecast for {lat}, {lon} - "
                           f"target range {hour_range}, found {forecast_time.hour}:00 "
                           f"(offset: {offset_hours:+d}h)")

            # Create result
            return ForecastResult(
                rain=selected_forecast["will_it_rain"] == 1,
                chance_of_rain=float(selected_forecast["chance_of_rain"]),
                precip_mm=float(selected_forecast["precip_mm"]),
                wind_kph=float(selected_forecast["wind_kph"]),
                temp_c=float(selected_forecast["temp_c"]),
                source="weatherapi",
                forecast_datetime=forecast_time,
                used_fallback=used_fallback,
                fallback_offset_hours=offset_hours
            )

        except Exception as e:
            logger.error(f"WeatherAPI: Error parsing response for {lat}, {lon}: {e}")
            return None
