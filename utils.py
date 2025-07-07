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
