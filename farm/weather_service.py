import logging
from datetime import datetime
import requests
from django.conf import settings
from .models import FarmCondition

logger = logging.getLogger(__name__)

# Regional aliases mapped to canonical search terms
LOCATION_ALIASES = {
    "coastal kenya": ("Mombasa", -4.0547, 39.6636, "Mombasa, Coastal Kenya"),
    "coast kenya": ("Mombasa", -4.0547, 39.6636, "Mombasa, Coastal Kenya"),
    "central kenya": ("Nyeri", -0.4201, 36.9476, "Nyeri, Central Kenya"),
    "western kenya": ("Kisumu", -0.0917, 34.7680, "Kisumu, Western Kenya"),
    "rift valley": ("Nakuru", -0.3031, 36.0800, "Nakuru, Rift Valley"),
    "eastern kenya": ("Machakos", -1.5177, 37.2634, "Machakos, Eastern Kenya"),
    "northern kenya": ("Isiolo", 0.3546, 37.5822, "Isiolo, Northern Kenya"),
}

WMO_WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Light freezing drizzle", "🌨️"),
    57: ("Dense freezing drizzle", "🌨️"),
    61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Light freezing rain", "🌧️"),
    67: ("Heavy freezing rain", "🌧️"),
    71: ("Slight snow fall", "❄️"),
    73: ("Moderate snow fall", "❄️"),
    75: ("Heavy snow fall", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


def wmo_to_condition(code: int) -> tuple[str, str]:
    """Returns (text_description, emoji_icon) for a WMO weather code."""
    return WMO_WEATHER_CODES.get(code, ("Partly cloudy", "⛅"))


def geocode_location(location_query: str) -> tuple[float, float, str]:
    """
    Resolves a location name into latitude, longitude, and formatted name.
    Handles regional descriptors (e.g. 'Coastal Kenya') and searches Open-Meteo's geocoding API.
    """
    clean_query = location_query.strip().lower()

    # 1. Check known regional aliases
    for alias, (term, lat, lon, display_name) in LOCATION_ALIASES.items():
        if alias in clean_query or clean_query in alias:
            return lat, lon, display_name

    # 2. Query Open-Meteo Geocoding API
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(location_query)}&count=1&language=en&format=json"
        res = requests.get(url, timeout=5)
        if res.ok:
            data = res.json()
            results = data.get("results")
            if results and len(results) > 0:
                first = results[0]
                lat = float(first.get("latitude"))
                lon = float(first.get("longitude"))
                name = first.get("name", location_query)
                country = first.get("country", "")
                display_name = f"{name}, {country}" if country else name
                return lat, lon, display_name
    except Exception as e:
        logger.warning(f"Geocoding failed for '{location_query}': {e}")

    # 3. Fallback to default Mombasa / Coastal Kenya coordinates
    return -4.0547, 39.6636, location_query.strip() or "Mombasa, Coastal Kenya"


def fetch_from_open_meteo(lat: float, lon: float, display_name: str) -> dict:
    """
    Fetches real-time weather and 7-day agricultural forecast from Open-Meteo API.
    No API key required; fast and globally accurate.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum"
        f"&timezone=auto"
    )
    res = requests.get(url, timeout=6)
    res.raise_for_status()
    data = res.json()

    current_data = data.get("current", {})
    daily_data = data.get("daily", {})

    temp = round(float(current_data.get("temperature_2m", 25.0)), 1)
    humidity = int(current_data.get("relative_humidity_2m", 65))
    wind_speed = round(float(current_data.get("wind_speed_10m", 10.0)), 1)
    weather_code = int(current_data.get("weather_code", 0))
    condition_text, condition_icon = wmo_to_condition(weather_code)

    # Precipitation chance from today's daily forecast
    daily_probs = daily_data.get("precipitation_probability_max", [])
    rainfall_chance = int(daily_probs[0]) if daily_probs else 10

    if rainfall_chance >= 60:
        rainfall_forecast = "High"
    elif rainfall_chance >= 30:
        rainfall_forecast = "Moderate"
    elif rainfall_chance > 5:
        rainfall_forecast = "Low"
    else:
        rainfall_forecast = "None"

    # Build 7-day daily forecast
    forecast_days = []
    dates = daily_data.get("time", [])
    max_temps = daily_data.get("temperature_2m_max", [])
    min_temps = daily_data.get("temperature_2m_min", [])
    probs = daily_data.get("precipitation_probability_max", [])
    codes = daily_data.get("weather_code", [])
    precip_sums = daily_data.get("precipitation_sum", [])

    for i in range(len(dates)):
        date_str = dates[i]
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = dt.strftime("%a")
            day_full = dt.strftime("%d %b")
        except Exception:
            day_name = date_str
            day_full = date_str

        code = codes[i] if i < len(codes) else 0
        day_text, day_icon = wmo_to_condition(code)

        forecast_days.append({
            "date": date_str,
            "day_name": day_name,
            "day_full": day_full,
            "temp_max": round(max_temps[i], 1) if i < len(max_temps) else temp,
            "temp_min": round(min_temps[i], 1) if i < len(min_temps) else temp,
            "rain_chance": probs[i] if i < len(probs) else 0,
            "precip_sum": round(precip_sums[i], 1) if i < len(precip_sums) else 0.0,
            "condition_text": day_text,
            "condition_icon": day_icon,
        })

    return {
        "success": True,
        "source": "Open-Meteo Live API",
        "location": display_name,
        "latitude": lat,
        "longitude": lon,
        "temperature": temp,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "rainfall_chance": rainfall_chance,
        "rainfall_forecast": rainfall_forecast,
        "condition_text": condition_text,
        "condition_icon": condition_icon,
        "forecast": forecast_days,
        "last_updated": datetime.now().strftime("%H:%M, %d %b %Y"),
    }


def fetch_from_open_weather_map(location_query: str, api_key: str) -> dict:
    """
    Fetches real-time weather from OpenWeatherMap API if the user configured an API key.
    """
    clean_query = location_query.strip()
    if clean_query.lower() in ["coastal kenya", "coast kenya"]:
        clean_query = "Mombasa,KE"

    url = f"https://api.openweathermap.org/data/2.5/weather?q={requests.utils.quote(clean_query)}&appid={api_key}&units=metric"
    res = requests.get(url, timeout=6)
    res.raise_for_status()
    data = res.json()

    main = data.get("main", {})
    wind = data.get("wind", {})
    weather_arr = data.get("weather", [{}])
    weather_item = weather_arr[0] if weather_arr else {}

    temp = round(float(main.get("temp", 25.0)), 1)
    humidity = int(main.get("humidity", 65))
    wind_kmh = round(float(wind.get("speed", 3.0)) * 3.6, 1)  # m/s to km/h
    condition_text = weather_item.get("description", "Partly cloudy").capitalize()

    # OpenWeather icon mapping
    icon_map = {
        "01": "☀️", "02": "🌤️", "03": "⛅", "04": "☁️",
        "09": "🌧️", "10": "🌦️", "11": "⛈️", "13": "❄️", "50": "🌫️"
    }
    icon_code = str(weather_item.get("icon", "02"))[:2]
    condition_icon = icon_map.get(icon_code, "⛅")

    clouds = int(data.get("clouds", {}).get("all", 20))
    rain_data = data.get("rain", {})
    rain_1h = rain_data.get("1h", 0)

    rainfall_chance = min(95, max(5, int(clouds * 0.7 + (40 if rain_1h > 0 else 0))))
    rainfall_forecast = "High" if rainfall_chance >= 60 else ("Moderate" if rainfall_chance >= 30 else "Low")

    name = data.get("name", location_query)
    sys_data = data.get("sys", {})
    country = sys_data.get("country", "")
    display_name = f"{name}, {country}" if country else name

    # Fetch 7-day forecast via Open-Meteo for rich agricultural planning
    coord = data.get("coord", {})
    lat = coord.get("lat")
    lon = coord.get("lon")
    forecast_days = []
    if lat and lon:
        try:
            om_data = fetch_from_open_meteo(lat, lon, display_name)
            forecast_days = om_data.get("forecast", [])
        except Exception:
            pass

    return {
        "success": True,
        "source": "OpenWeatherMap Live API",
        "location": display_name,
        "latitude": lat,
        "longitude": lon,
        "temperature": temp,
        "humidity": humidity,
        "wind_speed": wind_kmh,
        "rainfall_chance": rainfall_chance,
        "rainfall_forecast": rainfall_forecast,
        "condition_text": condition_text,
        "condition_icon": condition_icon,
        "forecast": forecast_days,
        "last_updated": datetime.now().strftime("%H:%M, %d %b %Y"),
    }


def fetch_live_weather(location_query: str = None) -> dict:
    """
    Main weather retrieval function.
    1. Checks if OPENWEATHERMAP_API_KEY is configured. If so, attempts OpenWeatherMap.
    2. Falls back seamlessly to Open-Meteo (open-source, 100% free, 0 setup required).
    """
    loc = (location_query or getattr(settings, 'DEFAULT_FARM_LOCATION', 'Mombasa, Coastal Kenya')).strip()
    owm_key = getattr(settings, 'OPENWEATHERMAP_API_KEY', '').strip()

    if owm_key and owm_key != 'your_openweathermap_api_key_here':
        try:
            return fetch_from_open_weather_map(loc, owm_key)
        except Exception as e:
            logger.warning(f"OpenWeatherMap failed ({e}), falling back to Open-Meteo.")

    # Primary reliable free live weather provider: Open-Meteo
    lat, lon, display_name = geocode_location(loc)
    return fetch_from_open_meteo(lat, lon, display_name)


def sync_live_weather(location_query: str = None) -> tuple[FarmCondition, dict]:
    """
    Fetches real-time weather from the external API and updates the active FarmCondition
    model in the AgriSmart database. This keeps all views (Dashboard, Weather page, Reports, AI)
    automatically synchronized with reality.
    """
    active_condition = FarmCondition.objects.filter(is_active=True).first()
    target_loc = location_query or (active_condition.location if active_condition else "Mombasa, Coastal Kenya")

    weather_data = fetch_live_weather(target_loc)

    if not active_condition:
        active_condition = FarmCondition.objects.create(
            location=weather_data["location"],
            condition_text=weather_data["condition_text"],
            temperature=weather_data["temperature"],
            soil_moisture=65,  # preserved or sensor default
            rainfall_forecast=weather_data["rainfall_forecast"],
            rainfall_chance=weather_data["rainfall_chance"],
            humidity=weather_data["humidity"],
            wind_speed=weather_data["wind_speed"],
            is_active=True,
        )
    else:
        active_condition.location = weather_data["location"]
        active_condition.condition_text = weather_data["condition_text"]
        active_condition.temperature = weather_data["temperature"]
        active_condition.rainfall_forecast = weather_data["rainfall_forecast"]
        active_condition.rainfall_chance = weather_data["rainfall_chance"]
        active_condition.humidity = weather_data["humidity"]
        active_condition.wind_speed = weather_data["wind_speed"]
        active_condition.save()

    return active_condition, weather_data
