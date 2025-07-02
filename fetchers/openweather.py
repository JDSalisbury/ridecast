
import requests
from datetime import datetime

from fetchers.base import WeatherFetcher
from config import OPENWEATHER_API_KEY

from utils import ForecastResult
# fetchers/openweather.py


class OpenWeather(WeatherFetcher):
    API_KEY = OPENWEATHER_API_KEY
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def get_forecast(self, lat, lon, hour_range=(8, 9)) -> ForecastResult | None:
        """
        Fetches weather data for the given lat/lon and hour range.
        hour_range: tuple of integers (start_hour, end_hour), 24-hour format.
        """
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
            for forecast in forecasts:
                time_str = forecast["dt_txt"]
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

                if dt.date() == datetime.now().date() and hour_range[0] <= dt.hour <= hour_range[1]:
                    rain = forecast.get("rain", {}).get("3h", 0) > 0
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
        return None
