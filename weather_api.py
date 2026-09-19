import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEO_URL = ("https://api.openweathermap.org/geo/1.0/direct")
WEATHER_URL = ("https://api.openweathermap.org/data/2.5/weather")

def get_coordinates(city):
    params = {"q": city, "limit": 1, "appid": API_KEY}
    response = requests.get(GEO_URL, params=params, timeout=10)

    response.raise_for_status()

    data = response.json()

    if not data:
        raise ValueError("도시를 찾을 수 없습니다.")

    location = data[0]

    return (
        location["lat"],
        location["lon"],
        location["name"]
    )

def get_current_weather(city):
    lat, lon, city_name = get_coordinates(city)

    params = {"lat": lat, "lon": lon, "appid": API_KEY,
              "units": "metric", "lang": "kr"}

    response = requests.get(WEATHER_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    return {
        "city": city_name,
        "weather": data["weather"][0]["main"],
        "description": data["weather"][0]["description"],
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
    }

