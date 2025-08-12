from abc import ABC, abstractmethod
from typing import Optional, Tuple
from models import ForecastResult


class WeatherFetcher(ABC):
    """Abstract base class for weather data fetchers."""
    
    source: str = "unknown"
    
    @abstractmethod
    def get_forecast(self, lat: float, lon: float, hour_range: Tuple[int, int] = (8, 9)) -> Optional[ForecastResult]:
        """
        Fetch weather forecast for given coordinates and time range.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate  
            hour_range: Tuple of (start_hour, end_hour) in 24-hour format
            
        Returns:
            ForecastResult if successful, None otherwise
        """
        pass
