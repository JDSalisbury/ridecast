import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TOMORROW_API_KEY = os.getenv("TOMORROW_API_KEY")
NOAA_API_KEY = os.getenv("NOAA_API_KEY")
OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
