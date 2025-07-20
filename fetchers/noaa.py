# fetchers/noaa.py
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from fetchers.base import WeatherFetcher
from utils import ForecastResult
from config import NOAA_API_KEY

LOCAL_TZ = ZoneInfo("America/New_York")


class NOAA(WeatherFetcher):
    source = "noaa"
    USER_AGENT = NOAA_API_KEY  # Stored in .env as contact info
    BASE_POINT_URL = "https://api.weather.gov/points/{lat},{lon}"
    HEADERS = {"User-Agent": USER_AGENT}

    def get_forecast(self, lat: float, lon: float, hour_range=(8, 9)) -> ForecastResult | None:
        try:
            # Step 1: Get forecast grid endpoint for this lat/lon
            point_url = self.BASE_POINT_URL.format(lat=lat, lon=lon)
            point_resp = requests.get(point_url, headers=self.HEADERS)
            point_resp.raise_for_status()
            point_data = point_resp.json()
            forecast_url = point_data["properties"]["forecastHourly"]

            # Step 2: Get hourly forecast
            forecast_resp = requests.get(forecast_url, headers=self.HEADERS)
            forecast_resp.raise_for_status()
            forecast_data = forecast_resp.json()

            periods = forecast_data["properties"]["periods"]
            now = datetime.now(LOCAL_TZ)

            for period in periods:
                dt_utc = datetime.fromisoformat(period["startTime"])
                dt_local = dt_utc.astimezone(LOCAL_TZ)

                if hour_range[0] <= dt_local.hour <= hour_range[1] and dt_local >= now:
                    rain = "rain" in period["shortForecast"].lower()
                    return ForecastResult(
                        rain=rain,
                        chance_of_rain=period.get(
                            "probabilityOfPrecipitation", {}).get("value", 0.0) or 0.0,
                        precip_mm=0.0,  # NOAA doesn't provide precip amount
                        wind_kph=float(period.get(
                            "windSpeed", "0 km/h").split(" ")[0]),
                        temp_c=(period["temperature"] - 32) * 5 /
                        9 if period["temperatureUnit"] == "F" else period["temperature"],
                        source="noaa"
                    )

        except Exception as e:
            print(f"[NOAA] Error: {e}")

        print(
            f"[NOAA] No matching forecast found for {lat}, {lon} in range {hour_range}")
        return None
