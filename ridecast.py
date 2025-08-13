# ridecast.py

import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any
from fetchers.openweather import OpenWeather
from fetchers.weatherapi import WeatherAPI
from fetchers.tomorrowio import TomorrowIO
from fetchers.noaa import NOAA
from models import ForecastResult, temp_to_fahrenheit, military_to_standard, kph_to_mph
from pathlib import Path
from evaluator import evaluate_ride, evaluate_ride_full_day2
from emailer import send_email
from logger import logger
from validation import validate_startup_requirements
from email_templates import create_ride_email_html, create_fallback_email_html, create_subject_line
FETCHERS = [
    OpenWeather(),
    WeatherAPI(),
    TomorrowIO(),
    NOAA(),
]


def parse_user_data(file_path: str = "users.json") -> List[Dict[str, Any]]:
    """Load and parse user data from a JSON file."""
    script_dir = Path(__file__).resolve().parent
    file_path = script_dir / file_path

    with open(file_path, "r") as f:
        raw_data = json.load(f)

    parsed_users = []
    for user in raw_data["users"]:
        # Parse tuple strings like "(7,9)" into actual tuples
        ride_in_hours = tuple(map(int, user["RIDE_IN_HOURS"].strip("()").split(",")))
        ride_back_hours = tuple(map(int, user["RIDE_BACK_HOURS"].strip("()").split(",")))
        
        # Parse location coordinate strings like "(39.949, -82.937)" into tuples
        locations = {}
        for location_name, coord_str in user["LOCATIONS"].items():
            coords = tuple(map(float, coord_str.strip("()").split(",")))
            locations[location_name] = coords

        parsed_user = {
            "id": user["id"],
            "name": user["NAME"],
            "email": user["EMAIL"],
            "enabled": user.get("ENABLED", True),
            "ride_in_hours": ride_in_hours,
            "ride_back_hours": ride_back_hours,
            "locations": locations,
        }
        parsed_users.append(parsed_user)

    return parsed_users


def get_all_forecasts(locations: Dict[str, Tuple[float, float]], hour_range: Tuple[int, int]) -> List[Tuple[str, ForecastResult]]:
    """Run all fetchers for each location during the specified hour range."""
    results = []
    for loc_name, (lat, lon) in locations.items():
        for fetcher in FETCHERS:
            logger.info(f"Fetching {loc_name} from {fetcher.source}...")
            result = fetcher.get_forecast(lat, lon, hour_range)
            if result:
                results.append((loc_name, result))
    return results


def print_summary(user: Dict[str, Any], forecasts: List[Tuple[str, ForecastResult]], label: str) -> str:
    # Get target hours for this summary
    target_hours = user['ride_in_hours'] if label == "Morning" else user['ride_back_hours']
    
    lines = [f"\n===== RideCast Forecast for {user['name']} ({label}) =====\n"]
    lines.append(
        f"Target riding time: {military_to_standard(target_hours[0])}:00 - {military_to_standard(target_hours[1])}:00")
    lines.append("")

    # Track API success/failure
    
    # Check which APIs should have been called
    from fetchers.openweather import OpenWeather
    from fetchers.weatherapi import WeatherAPI  
    from fetchers.tomorrowio import TomorrowIO
    from fetchers.noaa import NOAA
    
    all_sources = {f.source for f in [OpenWeather(), WeatherAPI(), TomorrowIO(), NOAA()]}
    successful_sources = {result.source for _, result in forecasts}
    failed_sources = all_sources - successful_sources

    if forecasts:
        lines.append("📊 WEATHER DATA SOURCES:")
        for loc_name, result in forecasts:
            rain_status = "🌧️ RAIN" if result.rain else "☀️ Clear"
            
            # Format forecast time info
            forecast_time = result.forecast_datetime.strftime("%b %d, %I:%M %p")
            time_info = f"@ {forecast_time}"
            
            # Add fallback info if used
            if result.used_fallback:
                fallback_sign = "+" if result.fallback_offset_hours > 0 else ""
                time_info += f" (fallback: {fallback_sign}{result.fallback_offset_hours}h)"
            
            lines.append(
                f"[{result.source.upper():.<15}] {loc_name}: {rain_status:.<15} | "
                f"{result.chance_of_rain:03.0f}% rain | {temp_to_fahrenheit(result.temp_c):.1f}°F | "
                f"{kph_to_mph(result.wind_kph):04.1f} mph | {time_info}"
            )
        
    
    # Show API status summary
    lines.append("")
    if successful_sources:
        lines.append(f"✅ APIs successful: {', '.join(sorted(successful_sources))}")
    if failed_sources:
        lines.append(f"❌ APIs failed: {', '.join(sorted(failed_sources))}")
    
    if not forecasts:
        lines.append("⚠️  No forecast data available from any API")
        lines.append(f"❌ All APIs failed: {', '.join(sorted(all_sources))}")
        
        # Return early for failed case
        summary = "\n".join(lines)
        logger.info(summary)
        return summary

    chat_evaluation = evaluate_ride(forecasts, label, user)
    lines.append(f"\n🤖 AI Evaluation:\n{chat_evaluation}\n")
    
    summary = "\n".join(lines)
    logger.info(summary)
    return summary


def is_weekend() -> bool:
    current_utc_time = datetime.now(timezone.utc)
    return current_utc_time.weekday() >= 5


if __name__ == "__main__":
    logger.info("=== Starting RideCast ===")
    
    # Validate startup requirements
    if not validate_startup_requirements():
        logger.error("Startup validation failed. Exiting.")
        exit(1)
    
    if is_weekend():
        logger.info("RideCast is not available on weekends. Exiting.")
        exit(0)

    users = parse_user_data()

    for user in users:
        if not user.get('enabled', True):
            logger.info(f"Skipping {user['name']} - user is disabled")
            continue
            
        logger.info(f"=== Running RideCast for {user['name']} ===")

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

        chat_evaluation = evaluate_ride_full_day2(full_report, user)

        # Parse the JSON response and send email
        logger.info(f"Sending RideCast to {user['email']}...")
        
        try:
            eval_data = json.loads(chat_evaluation)
            
            # Extract data with proper defaults
            should_ride = eval_data.get("should_ride", False)
            temp = eval_data.get("temp", "N/A")
            summary = eval_data.get("summary", "Weather forecast data available")
            fun_fact = eval_data.get("fun_fact", "Always wear proper protective gear when riding!")
            
            user_first_name = user['name'].split()[0]
            
            # Create formatted email
            subject = create_subject_line(should_ride, user_first_name, temp)
            html_body = create_ride_email_html(summary, fun_fact, user_first_name)
            
            send_email(user["email"], subject, html_body)
            logger.info(f"Successfully sent formatted RideCast to {user['name']}")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response from evaluator: {e}")
            logger.info("Using fallback email format")
            
            # Fallback to original behavior with better formatting
            user_first_name = user['name'].split()[0]
            subject = f"🏍️ RideCast Forecast for {user_first_name}"
            html_body = create_fallback_email_html(chat_evaluation, user_first_name)
            
            send_email(user["email"], subject, html_body)
            logger.info(f"Successfully sent fallback RideCast to {user['name']}")
            
        except Exception as e:
            logger.error(f"Unexpected error processing email for {user['name']}: {e}")
            continue
