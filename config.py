import os
from dotenv import load_dotenv

load_dotenv()


RIDE_IN_HOURS = (7, 9)
# Time window for ride back (4–7 PM)
RIDE_BACK_HOURS = (16, 18)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TOMORROW_API_KEY = os.getenv("TOMORROW_API_KEY")
NOAA_API_KEY = os.getenv("NOAA_API_KEY")
OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
