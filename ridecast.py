# ridecast.py

import json
from ast import literal_eval
from datetime import datetime, timezone
from fetchers.openweather import OpenWeather
from fetchers.weatherapi import WeatherAPI
from fetchers.tomorrowio import TomorrowIO
from fetchers.noaa import NOAA
from utils import ForecastResult, temp_to_fahrenheit, military_to_standard, kph_to_mph
from pathlib import Path
from evaluator import evaluate_ride, evaluate_ride_full_day

from emailer import send_email
FETCHERS = [
    OpenWeather(),
    WeatherAPI(),
    TomorrowIO(),
    NOAA(),
]


def parse_user_data(file_path="users.json"):
    """Load and parse user data from a JSON file."""
    script_dir = Path(__file__).resolve().parent
    file_path = script_dir / file_path

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
            print(f"[FETCH] Fetching {loc_name} from {fetcher.source}...")
            result = fetcher.get_forecast(lat, lon, hour_range)
            if result:
                results.append((loc_name, result))
    return results


def print_summary(user: dict, forecasts: list, label: str) -> str:
    lines = [f"\n===== RideCast Forecast for {user['name']} ({label}) =====\n"]
    if label == "Morning":
        lines.append(
            f"Forcast for riding in between {military_to_standard(user['ride_in_hours'][0])}:00 and {military_to_standard(user['ride_in_hours'][1])}:00")
    elif label == "Evening":
        lines.append(
            f"Forcast for riding in between {military_to_standard(user['ride_back_hours'][0])}:00 and {military_to_standard(user['ride_back_hours'][1])}:00")

    for loc_name, result in forecasts:
        rain_status = "🌧️ RAIN" if result.rain else "☀️ Clear"
        lines.append(f"[{result.source.upper():.<15}] {loc_name}: {rain_status.upper():.<10} | "
                     f"{result.chance_of_rain:03.0f}% rain | {temp_to_fahrenheit(result.temp_c):.1f}°F | "
                     f"{kph_to_mph(result.wind_kph):04.1f} mph wind")

    chat_evaluation = evaluate_ride(forecasts, label, user)
    lines.append(f"\nChatGPT Evaluation:\n{chat_evaluation}\n")
    print("\n".join(lines))
    return "\n".join(lines)


def is_weekend():
    current_utc_time = datetime.now(timezone.utc)
    return current_utc_time.weekday() >= 5


if __name__ == "__main__":

    if is_weekend():
        exit(0)

    users = parse_user_data()

    for user in users:
        print(f"\n=== Running RideCast for {user['name']} ===")

        full_report = []

        # Morning commute
        forecasts_morning = get_all_forecasts(
            user["locations"], user["ride_in_hours"])
        summary_morning = print_summary(
            user, forecasts_morning, label="Morning")
        full_report.append(summary_morning)

        # Evening commute
        forecasts_evening = get_all_forecasts(
            user["locations"], user["ride_back_hours"])
        summary_evening = print_summary(
            user, forecasts_evening, label="Evening")
        full_report.append(summary_evening)

        chat_evaluation = evaluate_ride_full_day(full_report, user)

        # Email the full report
        subject = f"🏍️ RideCast Forecast for {user['name'].split()[0]}"
        send_email(user["email"], subject,
                   chat_evaluation)
