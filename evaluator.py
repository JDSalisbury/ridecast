# Enhanced weather evaluator with motorcycle-specific safety analysis
from typing import List, Tuple, Dict, Any
from models import ForecastResult, temp_to_fahrenheit, military_to_standard
from openai import OpenAI
from config import OPEN_API_KEY
from logger import logger, load_fun_facts
import re

client = OpenAI(api_key=OPEN_API_KEY)

# Motorcycle-specific weather risk thresholds
WEATHER_THRESHOLDS = {
    'rain': {
        'low': 20,      # Light conditions - generally safe
        'moderate': 50,  # Moderate conditions - caution advised
        'high': 80,     # High risk conditions
    },
    'wind': {
        'comfortable': 15,  # mph - comfortable riding
        'caution': 25,      # mph - caution advised
        'dangerous': 35,    # mph - dangerous conditions
    },
    'temperature': {
        'cold_limit': 35,   # °F - too cold even with gear
        'cool_comfort': 50,  # °F - cool but comfortable with gear
        'hot_limit': 95,    # °F - too hot for safe riding
    }
}


def categorize_weather_risk(forecast: ForecastResult) -> Dict[str, str]:
    """Categorize weather conditions for motorcycle safety"""
    risk = {'overall': 'low', 'factors': []}

    # Rain risk assessment
    rain_chance = forecast.chance_of_rain
    if rain_chance >= WEATHER_THRESHOLDS['rain']['high']:
        risk['rain'] = 'high'
        risk['factors'].append(f"Heavy rain risk ({rain_chance}%)")
    elif rain_chance >= WEATHER_THRESHOLDS['rain']['moderate']:
        risk['rain'] = 'moderate'
        risk['factors'].append(f"Moderate rain risk ({rain_chance}%)")
    elif rain_chance >= WEATHER_THRESHOLDS['rain']['low']:
        risk['rain'] = 'low'
        risk['factors'].append(f"Light rain possible ({rain_chance}%)")
    else:
        risk['rain'] = 'minimal'

    # Wind risk assessment
    wind_mph = forecast.wind_kph * 0.621371  # Convert to mph
    if wind_mph >= WEATHER_THRESHOLDS['wind']['dangerous']:
        risk['wind'] = 'high'
        risk['factors'].append(f"Dangerous winds ({wind_mph:.0f} mph)")
    elif wind_mph >= WEATHER_THRESHOLDS['wind']['caution']:
        risk['wind'] = 'moderate'
        risk['factors'].append(f"Strong winds ({wind_mph:.0f} mph)")
    elif wind_mph >= WEATHER_THRESHOLDS['wind']['comfortable']:
        risk['wind'] = 'low'
        risk['factors'].append(f"Moderate winds ({wind_mph:.0f} mph)")
    else:
        risk['wind'] = 'minimal'

    # Temperature risk assessment
    temp_f = temp_to_fahrenheit(forecast.temp_c)
    if temp_f <= WEATHER_THRESHOLDS['temperature']['cold_limit']:
        risk['temperature'] = 'high'
        risk['factors'].append(f"Dangerously cold ({temp_f:.0f}°F)")
    elif temp_f >= WEATHER_THRESHOLDS['temperature']['hot_limit']:
        risk['temperature'] = 'high'
        risk['factors'].append(f"Dangerously hot ({temp_f:.0f}°F)")
    elif temp_f <= WEATHER_THRESHOLDS['temperature']['cool_comfort']:
        risk['temperature'] = 'moderate'
        risk['factors'].append(f"Cold conditions ({temp_f:.0f}°F)")
    else:
        risk['temperature'] = 'minimal'

    # Calculate overall risk
    risk_levels = [risk.get('rain', 'minimal'), risk.get(
        'wind', 'minimal'), risk.get('temperature', 'minimal')]
    if 'high' in risk_levels:
        risk['overall'] = 'high'
    elif 'moderate' in risk_levels:
        risk['overall'] = 'moderate'
    elif 'low' in risk_levels:
        risk['overall'] = 'low'
    else:
        risk['overall'] = 'minimal'

    return risk


def forecast_summary(forecasts: List[Tuple[str, ForecastResult]], label: str) -> str:
    """Enhanced forecast summary with risk categorization"""
    lines = [f"{label} Forecast Analysis:"]

    for loc_name, result in forecasts:
        # Get risk assessment
        risk_info = categorize_weather_risk(result)

        # Enhanced weather status
        if result.chance_of_rain >= WEATHER_THRESHOLDS['rain']['high']:
            weather_status = "⛈️ STORM RISK"
        elif result.chance_of_rain >= WEATHER_THRESHOLDS['rain']['moderate']:
            weather_status = "🌧️ RAIN LIKELY"
        elif result.chance_of_rain >= WEATHER_THRESHOLDS['rain']['low']:
            weather_status = "🌦️ RAIN POSSIBLE"
        else:
            weather_status = "☀️ CLEAR"

        # Wind indicator
        wind_mph = result.wind_kph * 0.621371
        if wind_mph >= WEATHER_THRESHOLDS['wind']['dangerous']:
            wind_status = "💨 DANGEROUS"
        elif wind_mph >= WEATHER_THRESHOLDS['wind']['caution']:
            wind_status = "💨 STRONG"
        else:
            wind_status = "💨 CALM"

        lines.append(
            f"- [{result.source.upper():12}] {loc_name}: {weather_status:12} | "
            f"{result.chance_of_rain:3.0f}% rain | {temp_to_fahrenheit(result.temp_c):5.1f}°F | "
            f"{wind_mph:4.1f} mph {wind_status} | Risk: {risk_info['overall'].upper()}"
        )

        # Add specific risk factors if any
        if risk_info['factors']:
            lines.append(f"    ⚠️  {', '.join(risk_info['factors'])}")

    return "\n".join(lines)


def call_openai(prompt: str, system_message: str = None) -> str:
    """Enhanced OpenAI API call with configurable system message"""
    default_system = (
        "You are an expert motorcycle safety advisor and a full-time professional meteorologist with deep weather analysis expertise. "
        "Your primary goal is rider safety while maximizing opportunities for safe riding. "
        "You understand that motorcycle commuting requires both morning and evening trips, "
        "so recommending a morning ride commits the rider to an evening return trip. "
        "You provide clear, actionable advice with specific reasoning based on weather patterns, "
        "road conditions, and motorcycle-specific safety considerations."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using GPT-3.5-turbo for compatibility
            messages=[
                {"role": "system", "content": system_message or default_system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3)  # Lower temperature for more consistent safety advice
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f"[OpenAI Error] {e}"


def evaluate_ride(forecasts: List[Tuple[str, ForecastResult]], label: str, rider: Dict[str, Any]) -> str:
    """Enhanced single-period evaluation with detailed risk analysis"""
    summary = forecast_summary(forecasts, label)

    # Analyze risk factors for this period
    risk_factors = []
    max_rain = 0
    max_wind = 0
    avg_temp = 0

    if forecasts:
        rain_chances = [f[1].chance_of_rain for f in forecasts]
        wind_speeds = [f[1].wind_kph *
                       0.621371 for f in forecasts]  # Convert to mph
        temperatures = [temp_to_fahrenheit(f[1].temp_c) for f in forecasts]

        max_rain = max(rain_chances)
        max_wind = max(wind_speeds)
        avg_temp = sum(temperatures) / len(temperatures)

        # Categorize risks
        if max_rain >= WEATHER_THRESHOLDS['rain']['high']:
            risk_factors.append(f"Heavy rain risk ({max_rain}%)")
        elif max_rain >= WEATHER_THRESHOLDS['rain']['moderate']:
            risk_factors.append(f"Moderate rain risk ({max_rain}%)")

        if max_wind >= WEATHER_THRESHOLDS['wind']['dangerous']:
            risk_factors.append(f"Dangerous winds ({max_wind:.0f} mph)")
        elif max_wind >= WEATHER_THRESHOLDS['wind']['caution']:
            risk_factors.append(f"Strong winds ({max_wind:.0f} mph)")

        if avg_temp <= WEATHER_THRESHOLDS['temperature']['cold_limit']:
            risk_factors.append(f"Dangerously cold ({avg_temp:.0f}°F)")
        elif avg_temp >= WEATHER_THRESHOLDS['temperature']['hot_limit']:
            risk_factors.append(f"Dangerously hot ({avg_temp:.0f}°F)")

    system_message = (
        "You are an expert motorcycle safety advisor and a full-time professional meteorologist providing weather-based riding recommendations. "
        "Consider rain percentage, wind speed, temperature, and visibility. "
        "Be encouraging when conditions are safe, but prioritize rider safety above all. "
        "Provide specific, actionable advice with clear reasoning."
    )

    prompt = (
        f"MOTORCYCLE {label.upper()} COMMUTE ANALYSIS\n"
        f"=================================\n\n"
        f"RIDER: {rider['name']}\n"
        f"TIME WINDOW: {military_to_standard(rider['ride_in_hours'][0] if label == 'Morning' else rider['ride_back_hours'][0])}:00 - "
        f"{military_to_standard(rider['ride_in_hours'][1] if label == 'Morning' else rider['ride_back_hours'][1])}:00\n"
        f"ROUTE: {' ↔ '.join(rider['locations'].keys())}\n\n"
        f"WEATHER DATA:\n{summary}\n\n"
        f"RISK FACTORS: {', '.join(risk_factors) if risk_factors else 'None identified'}\n\n"
        f"Provide a clear, friendly recommendation with specific reasoning. "
        f"Consider that this is a {label.lower()} commute and factor in appropriate safety margins."
    )

    return call_openai(prompt, system_message)


def analyze_full_day_weather(full_report: List[str]) -> Dict[str, Any]:
    """Extract and analyze weather data from full day reports"""
    analysis = {
        'morning_conditions': {},
        'evening_conditions': {},
        'overall_risk': 'minimal',
        'critical_factors': []
    }

    # Parse weather data from reports (simplified - could be enhanced with regex)
    morning_rain = evening_rain = 0
    morning_wind = evening_wind = 0
    morning_temp = evening_temp = 70

    for report in full_report:
        if 'Morning' in report:
            # Extract morning conditions
            rain_matches = re.findall(r'(\d+)% rain', report)
            wind_matches = re.findall(r'([\d.]+) mph', report)
            temp_matches = re.findall(r'([\d.]+)°F', report)

            if rain_matches:
                morning_rain = max([int(x) for x in rain_matches])
            if wind_matches:
                morning_wind = max([float(x) for x in wind_matches])
            if temp_matches:
                morning_temp = sum([float(x)
                                   for x in temp_matches]) / len(temp_matches)

        elif 'Evening' in report:
            # Extract evening conditions
            rain_matches = re.findall(r'(\d+)% rain', report)
            wind_matches = re.findall(r'([\d.]+) mph', report)
            temp_matches = re.findall(r'([\d.]+)°F', report)

            if rain_matches:
                evening_rain = max([int(x) for x in rain_matches])
            if wind_matches:
                evening_wind = max([float(x) for x in wind_matches])
            if temp_matches:
                evening_temp = sum([float(x)
                                   for x in temp_matches]) / len(temp_matches)

    analysis['morning_conditions'] = {
        'rain': morning_rain,
        'wind': morning_wind,
        'temp': morning_temp
    }

    analysis['evening_conditions'] = {
        'rain': evening_rain,
        'wind': evening_wind,
        'temp': evening_temp
    }

    # Determine critical factors
    if evening_rain >= WEATHER_THRESHOLDS['rain']['moderate']:
        analysis['critical_factors'].append(
            'Evening rain will trap you at work')
        analysis['overall_risk'] = 'high'

    if morning_rain >= WEATHER_THRESHOLDS['rain']['high'] or evening_rain >= WEATHER_THRESHOLDS['rain']['high']:
        analysis['critical_factors'].append('Heavy rain forecast')
        analysis['overall_risk'] = 'high'

    if morning_wind >= WEATHER_THRESHOLDS['wind']['dangerous'] or evening_wind >= WEATHER_THRESHOLDS['wind']['dangerous']:
        analysis['critical_factors'].append('Dangerous wind conditions')
        analysis['overall_risk'] = 'high'

    return analysis


def evaluate_ride_full_day2(full_report: List[str], rider: Dict[str, Any]) -> str:
    """Enhanced full-day evaluation with commitment-aware logic"""
    weather_analysis = analyze_full_day_weather(full_report)

    # Enhanced system message for full-day evaluation
    system_message = (
        "You are an expert motorcycle safety advisor and a full-time professional meteorologist analyzing weather for commuter riders. "
        "CRITICAL UNDERSTANDING: If you recommend riding TO work, the rider is is obligated to riding HOME. "
        "They cannot leave their motorcycle at work. This means BOTH the morning AND evening commute must be safe. "
        "If evening conditions are poor, recommend DON'T RIDE even if morning is perfect. "
        "Your goal is maximizing safe riding opportunities while prioritizing rider safety above all else. "
        "Be encouraging when conditions are truly safe, but conservative when there's meaningful risk. "
        "Focus on specific weather factors: rain percentage, wind speed, temperature, and timing."
    )

    fun_facts = load_fun_facts(rider['name'])
    prompt = (
        f"MOTORCYCLE COMMUTER WEATHER ANALYSIS\n"
        f"======================================\n\n"
        f"RIDER PROFILE:\n"
        f"• Name: {rider['name']}\n"
        f"• Morning commute: {military_to_standard(rider['ride_in_hours'][0])}:00 - {military_to_standard(rider['ride_in_hours'][1])}:00\n"
        f"• Evening commute: {military_to_standard(rider['ride_back_hours'][0])}:00 - {military_to_standard(rider['ride_back_hours'][1])}:00\n"
        f"• Route: {' ↔ '.join(rider['locations'].keys())}\n\n"
        f"WEATHER CONDITIONS:\n"
        f"{' '.join(full_report)}\n\n"
        f"ANALYSIS RESULTS:\n"
        f"{' '.join(weather_analysis)}\n\n"
        f"ANALYSIS REQUIREMENTS:\n"
        f"• Both morning AND evening must be acceptable for RIDE recommendation\n"
        f"• Evening conditions are weighted more heavily (tired rider, rush hour, darkness)\n"
        f"• Consider rain, wind, temperature, and visibility factors\n"
        f"• If evening rain >30%, strongly consider DON'T RIDE\n"
        f"• If either direction has >50% rain, recommend DON'T RIDE\n\n"
        f"Keep the summary concise verbose explanation of the decision. talk about the morning temp and ride in, along with the afternoon temp and ride out, but also chill and friendly, and cool. and fun. the summary is for an email."
        f"RESPONSE FORMAT - JSON only (no additional text):\n"
        f'{{\n'
        f'  "temp": "<Average temperature in Fahrenheit number only do not add F>",\n'
        f'  "should_ride": true or false,\n'
        f'  "risk_level": "<minimal/low/moderate/high/extreme>",\n'
        f'  "summary": "<Clear recommendation with specific reasoning about both commutes and weather analysis.>",\n'
        f'  "primary_concern": "<Main weather factor influencing decision>",\n'
        f'  "gear_recommendation": "<Specific gear advice if recommending ride>",\n'
        f'  "alternative_timing": "<Suggest better timing if conditions might improve>",\n'
        f'  "fun_fact": "<Motorcycle fact or riding tip/insight, or a motorcycle quote, do mention who said it. This is also a section to where you can have fun with it. and keep it fresh do not use any of the fun facts from the file {fun_facts}>"\n'
        f'}}'
    )

    return call_openai(prompt, system_message)
