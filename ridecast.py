# ridecast.py
from fetchers.openweather import OpenWeather
from fetchers.weatherapi import WeatherAPI
from fetchers.tomorrowio import TomorrowIO
from fetchers.noaa import NOAA
from utils import ForecastResult
from config import *

# Time window for ride in (4–7 PM)
RIDE_IN_HOURS = (8, 10)
LOCATIONS = {
    "Home": (39.94954786783218, -82.93728710268415),
    "Work": (40.14374280043774, -82.99466818733278),
    # "Checkpoint A": (40.04412439067341, -82.99702680589385),
    # "Checkpoint B": (40.07469880963292, -82.98800230120533),
}

FETCHERS = [
    OpenWeather(),
    WeatherAPI(),
    TomorrowIO(),
    NOAA(),
]


def get_all_forecasts(hour_range):
    results = []
    for loc_name, (lat, lon) in LOCATIONS.items():
        for fetcher in FETCHERS:
            print(f"Fetching {loc_name} from {fetcher.__class__.__name__}...")
            result = fetcher.get_forecast(lat, lon, hour_range)
            if result:
                print(
                    f"Got forecast from {fetcher.__class__.__name__} for {loc_name}: {result}")
                results.append((loc_name, result))
    return results


def print_summary(forecasts):
    print("\n===== RideCast Forecast =====\n")
    bad_conditions = 0
    early_exit_warnings = 0

    for loc_name, result in forecasts:
        rain_status = "🌧️ RAIN" if result.rain else "☀️ Clear"
        print(f"[{result.source.upper():.<15}] {loc_name}: {rain_status.upper():.<10} | "
              f"{result.chance_of_rain:02.0f}% rain | {result.temp_c:.1f}°C | "
              f"{result.wind_kph:04.1f} kph wind")

        if result.rain:
            bad_conditions += 1

    if bad_conditions == 0:
        print("\n✅ All clear – Good to ride in!")
    elif bad_conditions <= 2:
        print("\n⚠️ Some rain detected – Ride only if planning early return.")
    else:
        print("\n❌ Too risky – Better not to ride today.")


if __name__ == "__main__":
    forecasts = get_all_forecasts(RIDE_IN_HOURS)
    print_summary(forecasts)
