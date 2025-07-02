# tomorrowio weather fetcher
# fetchers/tomorrowio.py
import requests
from datetime import datetime, timezone
from fetchers.base import WeatherFetcher
from config import TOMORROW_API_KEY
from utils import ForecastResult


class TomorrowIO(WeatherFetcher):
    BASE_URL = "https://api.tomorrow.io/v4/weather/forecast"

    def get_forecast(self, lat: float, lon: float, hour_range=(8, 9)) -> ForecastResult | None:
        params = {
            "location": f"{lat},{lon}",
            "apikey": TOMORROW_API_KEY,
            "timesteps": "1h",
            "units": "metric",
            "fields": "precipitationProbability,precipitationIntensity,temperature,windSpeed"
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            timelines = data.get("timelines", {}).get("hourly", [])
            now = datetime.now().astimezone(timezone.utc)
            local_today = now.date()

            for forecast in timelines:
                dt = datetime.fromisoformat(
                    forecast["time"].replace("Z", "+00:00"))
                if dt.date() == local_today and hour_range[0] <= dt.hour <= hour_range[1]:
                    precip_prob = forecast.get("values", {}).get(
                        "precipitationProbability", 0.0)
                    precip_intensity = forecast.get("values", {}).get(
                        "precipitationIntensity", 0.0)

                    return ForecastResult(
                        rain=precip_prob >= 30 or precip_intensity > 0.0,
                        chance_of_rain=precip_prob,
                        precip_mm=precip_intensity,
                        wind_kph=forecast["values"].get("windSpeed", 0.0),
                        temp_c=forecast["values"].get("temperature", 0.0),
                        source="tomorrowio"
                    )

        except Exception as e:
            print(f"[TomorrowIO] Error: {e}")
        return None
