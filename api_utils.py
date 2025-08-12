"""Utilities for weather API calls including retry logic and error handling."""

import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, Tuple
from logger import logger
from weather_config import WeatherConfig


def retry_with_backoff(
    func: Callable,
    config: WeatherConfig,
    operation_name: str
) -> Optional[requests.Response]:
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: Function to execute (should return requests.Response)
        config: WeatherConfig with retry settings
        operation_name: Name of operation for logging
        
    Returns:
        Response object if successful, None if all retries failed
    """
    if not config.enable_retries:
        try:
            return func()
        except Exception as e:
            logger.error(f"{operation_name} failed: {e}")
            return None
    
    delay = config.retry_delay_base
    
    for attempt in range(config.max_retries + 1):  # +1 for initial attempt
        try:
            response = func()
            response.raise_for_status()
            if attempt > 0:
                logger.info(f"{operation_name} succeeded on attempt {attempt + 1}")
            return response
            
        except requests.exceptions.Timeout:
            logger.warning(f"{operation_name} timeout on attempt {attempt + 1}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"{operation_name} connection error on attempt {attempt + 1}")
        except requests.exceptions.HTTPError as e:
            logger.warning(f"{operation_name} HTTP error on attempt {attempt + 1}: {e.response.status_code}")
            # Don't retry on 4xx client errors (except rate limiting)
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                logger.error(f"{operation_name} failed with client error, not retrying")
                return None
        except Exception as e:
            logger.warning(f"{operation_name} unexpected error on attempt {attempt + 1}: {e}")
        
        # Don't sleep after the last attempt
        if attempt < config.max_retries:
            logger.info(f"{operation_name} retrying in {delay:.1f}s...")
            time.sleep(delay)
            delay = min(delay * 2, config.retry_delay_max)  # Exponential backoff with cap
    
    logger.error(f"{operation_name} failed after {config.max_retries + 1} attempts")
    return None


def find_forecast_with_fallback(
    forecasts: list,
    target_hour_range: Tuple[int, int],
    current_time: datetime,
    config: WeatherConfig,
    time_extractor: Callable[[Any], datetime]
) -> Tuple[Optional[Any], bool, Optional[int]]:
    """
    Find a forecast within target hours, or use fallback logic to find next best option.
    
    Args:
        forecasts: List of forecast data from API
        target_hour_range: Tuple of (start_hour, end_hour) for target time
        current_time: Current datetime for filtering future forecasts
        config: WeatherConfig with fallback settings
        time_extractor: Function to extract datetime from forecast item
        
    Returns:
        Tuple of (forecast_item, used_fallback, offset_hours)
    """
    start_hour, end_hour = target_hour_range
    
    # First pass: Look for exact match in target range
    for forecast in forecasts:
        forecast_time = time_extractor(forecast)
        
        # Skip past forecasts
        if forecast_time < current_time:
            continue
            
        # Check if in target range
        if start_hour <= forecast_time.hour <= end_hour:
            return forecast, False, None
    
    # Second pass: Use fallback logic if enabled
    if not config.enable_fallback:
        return None, False, None
    
    # Find closest forecast within fallback window
    best_forecast = None
    best_offset = None
    min_distance = float('inf')
    
    target_start = current_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    target_end = current_time.replace(hour=end_hour, minute=59, second=59, microsecond=999999)
    
    # If target range is in the past, shift to tomorrow
    if target_end < current_time:
        target_start += timedelta(days=1)
        target_end += timedelta(days=1)
    
    fallback_start = target_start - timedelta(hours=config.fallback_window_hours)
    fallback_end = target_end + timedelta(hours=config.fallback_window_hours)
    
    for forecast in forecasts:
        forecast_time = time_extractor(forecast)
        
        # Skip past forecasts
        if forecast_time < current_time:
            continue
            
        # Check if within fallback window
        if fallback_start <= forecast_time <= fallback_end:
            # Calculate distance from ideal target (middle of range)
            target_center = target_start + (target_end - target_start) / 2
            distance = abs((forecast_time - target_center).total_seconds())
            
            if distance < min_distance:
                min_distance = distance
                best_forecast = forecast
                # Calculate offset in hours from target range
                if forecast_time < target_start:
                    best_offset = -int((target_start - forecast_time).total_seconds() // 3600)
                elif forecast_time > target_end:
                    best_offset = int((forecast_time - target_end).total_seconds() // 3600)
                else:
                    best_offset = 0  # Actually in range (shouldn't happen in fallback)
    
    if best_forecast:
        return best_forecast, True, best_offset
    
    return None, False, None