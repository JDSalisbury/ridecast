import requests
from datetime import datetime
from fetchers.base import WeatherFetcher
from config import WEATHER_API_KEY
from models import ForecastResult
from logger import logger


class WeatherAPI(WeatherFetcher):
    source = "weatherapi"
    BASE_URL = "https://api.weatherapi.com/v1/forecast.json"

    def get_forecast(self, lat: float, lon: float, hour_range=(8, 9)) -> ForecastResult | None:
        params = {
            "key": WEATHER_API_KEY,
            "q": f"{lat},{lon}",
            "days": 1,
            "aqi": "no",
            "alerts": "no"
        }
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            forecast_hours = (
                data.get("forecast", {})
                    .get("forecastday", [])[0]
                    .get("hour", [])
            )

            today = datetime.now().date()

            for hour in forecast_hours:
                dt = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
                if dt.date() == today and hour_range[0] <= dt.hour <= hour_range[1]:
                    return ForecastResult(
                        rain=hour["will_it_rain"] == 1,
                        chance_of_rain=float(hour["chance_of_rain"]),
                        precip_mm=float(hour["precip_mm"]),
                        wind_kph=float(hour["wind_kph"]),
                        temp_c=float(hour["temp_c"]),
                        source="weatherapi"
                    )

        except Exception as e:
            logger.error(f"WeatherAPI error: {e}")
        return None
