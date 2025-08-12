"""Environment variable and configuration validation."""

import os
import sys
from typing import List
from logger import logger


def validate_required_env_vars() -> bool:
    """Validate that all required environment variables are set."""
    required_vars = [
        "EMAIL_HOST",
        "EMAIL_PORT", 
        "EMAIL_USERNAME",
        "EMAIL_PASSWORD",
        "EMAIL_FROM",
        "OPENWEATHER_API_KEY",
        "WEATHER_API_KEY", 
        "TOMORROW_API_KEY",
        "NOAA_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    missing_vars: List[str] = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("Please ensure all required variables are set in your .env file")
        return False
    
    logger.info("All required environment variables validated successfully")
    return True


def validate_users_file(file_path: str = "users.json") -> bool:
    """Validate that the users.json file exists and is readable."""
    from pathlib import Path
    
    script_dir = Path(__file__).resolve().parent
    users_file = script_dir / file_path
    
    if not users_file.exists():
        logger.error(f"Users file not found: {users_file}")
        return False
    
    try:
        import json
        with open(users_file, "r") as f:
            data = json.load(f)
            
        if "users" not in data:
            logger.error("Users file missing 'users' key")
            return False
            
        if not isinstance(data["users"], list) or len(data["users"]) == 0:
            logger.error("No users found in users file")
            return False
            
        logger.info(f"Users file validated successfully: {len(data['users'])} users found")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in users file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading users file: {e}")
        return False


def validate_startup_requirements() -> bool:
    """Validate all startup requirements."""
    logger.info("Validating startup requirements...")
    
    if not validate_required_env_vars():
        return False
        
    if not validate_users_file():
        return False
        
    logger.info("All startup requirements validated successfully")
    return True