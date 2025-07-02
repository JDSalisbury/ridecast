from dataclasses import dataclass


@dataclass
class ForecastResult:
    rain: bool
    chance_of_rain: float  # 0–100%
    precip_mm: float
    wind_kph: float
    temp_c: float
    source: str
