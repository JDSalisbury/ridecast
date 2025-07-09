# ridecast.py

import json
from ast import literal_eval
from fetchers.openweather import OpenWeather
from fetchers.weatherapi import WeatherAPI
from fetchers.tomorrowio import TomorrowIO
from fetchers.noaa import NOAA
from utils import ForecastResult, temp_to_fahrenheit, military_to_standard, kph_to_mph
from pathlib import Path
from evaluator import evaluate_ride

FETCHERS = [
    OpenWeather(),
    WeatherAPI(),
    TomorrowIO(),
    NOAA(),
]


def parse_user_data(file_path="users.json"):
    """Load and parse user data from a JSON file."""
    with open(file_path, "r") as f:
        raw_data = json.load(f)

    parsed_users = []
    for user in raw_data["users"]:
        parsed_user = {
            "id": user["id"],
            "name": user["NAME"],
            "email": user["EMAIL"],
            "ride_in_hours": literal_eval(user["RIDE_IN_HOURS"]),
            "ride_back_hours": literal_eval(user["RIDE_BACK_HOURS"]),
            "locations": {k: literal_eval(v) for k, v in user["LOCATIONS"].items()},
        }
        parsed_users.append(parsed_user)

    return parsed_users


def get_all_forecasts(locations: dict, hour_range: tuple) -> list[tuple[str, ForecastResult]]:
    """Run all fetchers for each location during the specified hour range."""
    results = []
    for loc_name, (lat, lon) in locations.items():
        for fetcher in FETCHERS:
            result = fetcher.get_forecast(lat, lon, hour_range)
            if result:
                results.append((loc_name, result))
    return results


def print_summary(user: dict, forecasts: list, label: str):
    print(f"\n===== RideCast Forecast for {user['name']} ({label}) =====\n")
    if label == "Morning":
        print(
            f"Forcast for riding in between {military_to_standard(user['ride_in_hours'][0])}:00 and {military_to_standard(user['ride_in_hours'][1])}:00")
    elif label == "Evening":
        print(
            f"Forcast for riding in between {military_to_standard(user['ride_back_hours'][0])}:00 and {military_to_standard(user['ride_back_hours'][1])}:00")

    for loc_name, result in forecasts:
        rain_status = "🌧️ RAIN" if result.rain else "☀️ Clear"
        print(f"[{result.source.upper():.<15}] {loc_name}: {rain_status.upper():.<10} | "
              f"{result.chance_of_rain:03.0f}% rain | {temp_to_fahrenheit(result.temp_c):.1f}°F | "
              f"{kph_to_mph(result.wind_kph):04.1f} mph wind")

    chat_evaluation = evaluate_ride(forecasts, label, user)
    print(f"\nChatGPT Evaluation:\n{chat_evaluation}\n")


if __name__ == "__main__":
    users = parse_user_data()

    for user in users:
        # Morning commute
        forecasts = get_all_forecasts(user["locations"], user["ride_in_hours"])
        print_summary(user, forecasts, label="Morning")

        # Evening commute
        forecasts = get_all_forecasts(
            user["locations"], user["ride_back_hours"])
        print_summary(user, forecasts, label="Evening")
