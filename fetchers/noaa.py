# fetchers/noaa.py
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Tuple
from fetchers.base import WeatherFetcher
from models import ForecastResult
from config import NOAA_API_KEY
from logger import logger
from api_utils import retry_with_backoff, find_forecast_with_fallback
from weather_config import default_config

LOCAL_TZ = ZoneInfo("America/New_York")


class NOAA(WeatherFetcher):
    source = "noaa"
    USER_AGENT = NOAA_API_KEY  # Stored in .env as contact info
    BASE_POINT_URL = "https://api.weather.gov/points/{lat},{lon}"
    HEADERS = {"User-Agent": USER_AGENT}

    def get_forecast(self, lat: float, lon: float, hour_range: Tuple[int, int] = (8, 9)) -> ForecastResult | None:
        if "noaa" not in default_config.enabled_apis:
            logger.info("NOAA API disabled in configuration")
            return None

        try:
            # Step 1: Get forecast grid endpoint for this lat/lon
            point_url = self.BASE_POINT_URL.format(lat=lat, lon=lon)
            
            def make_point_request():
                return requests.get(
                    point_url, 
                    headers=self.HEADERS,
                    timeout=default_config.api_timeout_seconds
                )

            point_resp = retry_with_backoff(
                make_point_request,
                default_config,
                f"NOAA point lookup for {lat}, {lon}"
            )
            
            if not point_resp:
                return None

            point_data = point_resp.json()
            forecast_url = point_data["properties"]["forecastHourly"]

            # Step 2: Get hourly forecast
            def make_forecast_request():
                return requests.get(
                    forecast_url, 
                    headers=self.HEADERS,
                    timeout=default_config.api_timeout_seconds
                )

            forecast_resp = retry_with_backoff(
                make_forecast_request,
                default_config,
                f"NOAA forecast for {lat}, {lon}"
            )
            
            if not forecast_resp:
                return None

            forecast_data = forecast_resp.json()
            periods = forecast_data["properties"]["periods"]
            
            if not periods:
                logger.warning(f"NOAA: No forecast periods returned for {lat}, {lon}")
                return None

            now = datetime.now(LOCAL_TZ)

            # Helper function to extract datetime from period
            def extract_time(period):
                dt_utc = datetime.fromisoformat(period["startTime"])
                return dt_utc.astimezone(LOCAL_TZ)

            # Find forecast with fallback logic
            selected_period, used_fallback, offset_hours = find_forecast_with_fallback(
                periods, hour_range, now, default_config, extract_time
            )

            if not selected_period:
                logger.warning(
                    f"NOAA: No suitable forecast found for {lat}, {lon} in range {hour_range} "
                    f"(checked {len(periods)} periods, fallback enabled: {default_config.enable_fallback})"
                )
                return None

            # Log fallback usage
            forecast_time = extract_time(selected_period)
            if used_fallback:
                logger.info(f"NOAA: Using fallback forecast for {lat}, {lon} - "
                           f"target range {hour_range}, found {forecast_time.hour}:00 "
                           f"(offset: {offset_hours:+d}h)")

            # Create result
            rain = "rain" in selected_period["shortForecast"].lower()
            
            # Parse wind speed (format: "X mph" or "X to Y mph")  
            wind_str = selected_period.get("windSpeed", "0 mph")
            try:
                wind_mph = float(wind_str.split(" ")[0])
                wind_kph = wind_mph * 1.60934  # Convert mph to kph
            except (ValueError, IndexError):
                wind_kph = 0.0
                logger.warning(f"NOAA: Could not parse wind speed '{wind_str}'")

            # Convert temperature if needed
            temp_f = selected_period["temperature"]
            temp_c = (temp_f - 32) * 5 / 9 if selected_period["temperatureUnit"] == "F" else temp_f

            return ForecastResult(
                rain=rain,
                chance_of_rain=selected_period.get("probabilityOfPrecipitation", {}).get("value", 0.0) or 0.0,
                precip_mm=0.0,  # NOAA doesn't provide precip amount
                wind_kph=wind_kph,
                temp_c=temp_c,
                source="noaa",
                forecast_datetime=forecast_time,
                used_fallback=used_fallback,
                fallback_offset_hours=offset_hours
            )

        except Exception as e:
            logger.error(f"NOAA: Error processing forecast for {lat}, {lon}: {e}")
            return None
