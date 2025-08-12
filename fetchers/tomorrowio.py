# fetchers/tomorrowio.py
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fetchers.base import WeatherFetcher
from config import TOMORROW_API_KEY
from models import ForecastResult
from logger import logger

LOCAL_TZ = ZoneInfo("America/New_York")


class TomorrowIO(WeatherFetcher):
    source = "tomorrowio"
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
            now = datetime.now(LOCAL_TZ)

            for forecast in timelines:
                dt_utc = datetime.fromisoformat(
                    forecast["time"].replace("Z", "+00:00"))
                dt_local = dt_utc.astimezone(LOCAL_TZ)

                if hour_range[0] <= dt_local.hour <= hour_range[1] and dt_local >= now:
                    values = forecast.get("values", {})
                    precip_prob = values.get("precipitationProbability", 0.0)
                    precip_intensity = values.get(
                        "precipitationIntensity", 0.0)

                    return ForecastResult(
                        rain=precip_prob >= 30 or precip_intensity > 0.0,
                        chance_of_rain=precip_prob,
                        precip_mm=precip_intensity,
                        wind_kph=values.get("windSpeed", 0.0),
                        temp_c=values.get("temperature", 0.0),
                        source="tomorrowio"
                    )

        except Exception as e:
            logger.error(f"TomorrowIO API error: {e}")
            if 'response' in locals():
                logger.error(f"TomorrowIO response status: {response.status_code}")

        logger.warning(
            f"TomorrowIO: No matching forecast found for {lat}, {lon} in range {hour_range}")
        return None
