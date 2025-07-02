# fetchers/openweather.py
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fetchers.base import WeatherFetcher
from config import OPENWEATHER_API_KEY
from utils import ForecastResult

LOCAL_TZ = ZoneInfo("America/New_York")


class OpenWeather(WeatherFetcher):
    API_KEY = OPENWEATHER_API_KEY
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def get_forecast(self, lat: float, lon: float, hour_range=(8, 9)) -> ForecastResult | None:
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.API_KEY,
            "units": "metric"
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            forecasts = data.get("list", [])
            now = datetime.now(LOCAL_TZ)

            for forecast in forecasts:
                dt_utc = datetime.strptime(
                    forecast["dt_txt"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                dt_local = dt_utc.astimezone(LOCAL_TZ)

                if hour_range[0] <= dt_local.hour <= hour_range[1] and dt_local >= now:
                    rain = forecast.get("rain", {}).get("3h", 0.0) > 0
                    return ForecastResult(
                        rain=rain,
                        chance_of_rain=forecast.get("pop", 0.0) * 100,
                        precip_mm=forecast.get("rain", {}).get("3h", 0.0),
                        wind_kph=forecast["wind"]["speed"] * 3.6,
                        temp_c=forecast["main"]["temp"],
                        source="openweather"
                    )

        except Exception as e:
            print(f"[OpenWeather] Error: {e}")
            print(f"[OpenWeather] Response status: {response.status_code}")

        print(
            f"[OpenWeather] No matching forecast found for {lat}, {lon} in range {hour_range}")
        return None
