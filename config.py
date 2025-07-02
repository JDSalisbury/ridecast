import os
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TOMORROW_API_KEY = os.getenv("TOMORROW_API_KEY")
NOAA_API_KEY = os.getenv("NOAA_API_KEY")
