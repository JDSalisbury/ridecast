"""Configuration settings for weather API behavior."""

from dataclasses import dataclass
from typing import List


@dataclass
class WeatherConfig:
    """Configuration for weather API fetching behavior."""
    
    # Fallback settings
    enable_fallback: bool = True
    fallback_window_hours: int = 3  # How many hours before/after target to search
    
    # Retry settings  
    enable_retries: bool = True
    max_retries: int = 2
    retry_delay_base: float = 1.0  # Base delay in seconds for exponential backoff
    retry_delay_max: float = 10.0  # Maximum delay between retries
    
    # Timeout settings
    api_timeout_seconds: float = 15.0
    
    # Enabled APIs (can disable problematic ones)
    enabled_apis: List[str] = None  # None means all enabled
    
    def __post_init__(self):
        if self.enabled_apis is None:
            self.enabled_apis = ["openweather", "weatherapi", "tomorrowio", "noaa"]


# Default configuration instance
default_config = WeatherConfig()