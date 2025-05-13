
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
print(API_KEY)

# def get_weather(city="Denton"):
#     url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
#     response = requests.get(url)

#     if response.status_code != 200:
#         return "⚠️ Unable to fetch weather info."

#     data = response.json()
#     main = data["main"]
#     weather = data["weather"][0]["description"]

#     temp = main["temp"]
#     feels_like = main["feels_like"]
#     humidity = main["humidity"]

#     return f"🌤️ Weather in {city}: {weather}, {temp}°C (feels like {feels_like}°C), humidity: {humidity}%"

def get_weather_by_coords(lat, lon):
    print(API_KEY)
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    print(url)
    response = requests.get(url)
    print(f"Fetching weather for coordinates: {lat}, {lon},{response}")
    if response.status_code != 200:
        return { "city": "Unknown", "error": "Failed to fetch weather" }

    data = response.json()
    main = data["main"]
    weather = data["weather"][0]
    city = data["name"]

    return {
        "city": city,
        "description": weather["description"].capitalize(),
        "temp": main["temp"],
        "feels_like": main["feels_like"],
        "humidity": main["humidity"],
        "icon": weather["icon"]
    }