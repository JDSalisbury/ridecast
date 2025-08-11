# aggrigate data and evalute if one should ride in.
from utils import ForecastResult, temp_to_fahrenheit, military_to_standard
import os
from openai import OpenAI
from config import OPEN_API_KEY
client = OpenAI(api_key=OPEN_API_KEY)


def forecast_summary(forecasts: list[tuple[str, ForecastResult]], label: str) -> str:
    lines = [f"{label} Forecast:"]
    for loc_name, result in forecasts:
        rain_status = "Rain" if result.rain else "Clear"
        lines.append(
            f"- [{result.source.upper()}] {loc_name}: {rain_status} | "
            f"{result.chance_of_rain:.0f}% rain | {temp_to_fahrenheit(result.temp_c):.1f}°F | "
            f"{result.wind_kph:.1f} kph wind"
        )
    return "\n".join(lines)


def call_openai(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a motorcycle commuting assistant who prioritizes safety."},
                {"role": "user",
                 "content": prompt}
            ],
            temperature=0.5)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[OpenAI Error] {e}"


def evaluate_ride(forecasts: list[tuple[str, ForecastResult]], label: str, rider: dict) -> str:
    summary = forecast_summary(forecasts, label)
    prompt = (
        f"Given the following motorcycle commute weather forecasts for {label}, should the user ride or not?\n"
        f"Here is some information about the rider:\n"
        f"Name: {rider['name']}\n"
        f"Email: {rider['email']}\n"
        f"Preferred Riding Hours: {military_to_standard(rider['ride_in_hours'][0])}:00 - {military_to_standard(rider['ride_in_hours'][1])}:00\n"
        f"Locations: {', '.join(rider['locations'].keys())}\n"
        f"\n"
        f"Be excitied to help the user make a safe decision, and know that the user wants to ride in comfort and safety.\n"
        f"Be concise and consider rain, temperature, and wind.\n"
        f"\n"
        f"{summary}\n\n"
        f"Respond with a clear recommendation for the rider. Keep it chill though."
    )

    return call_openai(prompt)


def evaluate_ride_full_day(full_report: list[str], rider: dict) -> str:
    prompt = (
        f"Given the following full day motorcycle commute weather forecasts, should the user ride or not?\n"
        f"Here is some information about the rider:\n"
        f"Name: {rider['name']}\n"
        f"Email: {rider['email']}\n"
        f"Preferred Riding Hours: {military_to_standard(rider['ride_in_hours'][0])}:00 - {military_to_standard(rider['ride_in_hours'][1])}:00\n"
        f"Locations: {', '.join(rider['locations'].keys())}\n"
        f"\n"
        f"Be excitied to help the user make a safe decision, and know that the user wants to ride in comfort and safety.\n"
        f"Be concise and consider rain, temperature, and wind.\n"
        f"Given it's a full day report, consider both morning and evening forecasts, if its raining in the evening, don't suggest riding in.\n"
        f"\n"
        f"{' '.join(full_report)}\n\n"
        f"Respond with a clear recommendation for the rider. Keep it chill though. Could you add a fun motorcycle fact at the end of your response. Make sure the fact is actually true?"
    )

    return call_openai(prompt)


def evaluate_ride_full_day2(full_report: list[str], rider: dict) -> str:
    prompt = (
        f"Given the following full day motorcycle commute weather forecasts, should the user ride or not?\n"
        f"Here is some information about the rider:\n"
        f"Name: {rider['name']}\n"
        f"Email: {rider['email']}\n"
        f"Preferred Riding Hours: {military_to_standard(rider['ride_in_hours'][0])}:00 - {military_to_standard(rider['ride_in_hours'][1])}:00\n"
        f"Locations: {', '.join(rider['locations'].keys())}\n"
        f"\n"
        f"The user wants to ride in comfort and safety. Be concise and consider rain, temperature, and wind.\n"
        f"Since it's a full day report, factor in both morning and evening forecasts. If it's raining in the evening, do not suggest riding in the morning.\n"
        f"\n"
        f"{' '.join(full_report)}\n\n"
        f"Respond ONLY with a JSON object in the following format (do not include any explanation or extra text):\n"
        f'{{\n'
        f'  "temp": "<Temperature in Fahrenheit>",\n'
        f'  "should_ride": true or false,\n'
        f'  "summary": "<a friendly summary recommendation on the weather throughout the day on your route>",\n'
        f'  "fun_fact": "<a true, fun motorcycle fact/or motorcycle tips that can help the user ride safely and more efficiently>"\n'
        f'}}'
    )

    return call_openai(prompt)
