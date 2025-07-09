from dataclasses import dataclass


@dataclass
class ForecastResult:
    rain: bool
    chance_of_rain: float  # 0–100%
    precip_mm: float
    wind_kph: float
    temp_c: float
    source: str


def temp_to_fahrenheit(temp_c: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (temp_c * 9/5) + 32


def kph_to_mph(speed_kph: float) -> float:
    """Convert kilometers per hour to miles per hour."""
    return speed_kph * 0.621371


def military_to_standard(hour: int) -> int:
    """Convert 24-hour military time to 12-hour standard time."""
    if hour == 0:
        return 12  # Midnight
    elif hour > 12:
        return hour - 12
    else:
        return hour
