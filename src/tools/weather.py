import requests
from datetime import datetime

GEOCODE_URL  = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO = {
    0: "clear sky",
    1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "icy fog",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    77: "snow grains",
    80: "rain showers", 81: "moderate showers", 82: "heavy showers",
    85: "snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
}


def _geocode(city: str) -> tuple[float, float, str]:
    r = requests.get(GEOCODE_URL,
                     params={"name": city, "count": 1, "language": "en"},
                     timeout=5)
    results = r.json().get("results", [])
    if not results:
        raise ValueError(f"City not found: {city}")
    loc = results[0]
    return loc["latitude"], loc["longitude"], loc.get("timezone", "auto")


def get_weather(city: str = "Bangalore", forecast_days: int = 0) -> str:
    """
    forecast_days=0  → current conditions only
    forecast_days=1  → current + tomorrow
    forecast_days=3  → current + next 3 days
    """
    try:
        lat, lon, timezone = _geocode(city)

        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone,
            "current": "temperature_2m,apparent_temperature,weather_code,"
                       "relative_humidity_2m,wind_speed_10m",
            "forecast_days": max(1, forecast_days + 1),
        }
        if forecast_days > 0:
            params["daily"] = (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,precipitation_sum"
            )

        r = requests.get(FORECAST_URL, params=params, timeout=5)
        data = r.json()

        c    = data["current"]
        desc = WMO.get(c["weather_code"], "unknown conditions")
        current_line = (
            f"{desc}, {round(c['temperature_2m'])}°C "
            f"(feels like {round(c['apparent_temperature'])}°C), "
            f"humidity {c['relative_humidity_2m']}%, "
            f"wind {round(c['wind_speed_10m'])} km/h"
        )

        if forecast_days == 0:
            return current_line

        parts = [f"Right now in {city}: {current_line}."]

        daily = data["daily"]
        for i, date in enumerate(daily["time"]):
            if i == 0:
                label = "Today"
            elif i == 1:
                label = "Tomorrow"
            else:
                label = datetime.fromisoformat(date).strftime("%A")

            wc        = daily["weather_code"][i]
            tmax      = round(daily["temperature_2m_max"][i])
            tmin      = round(daily["temperature_2m_min"][i])
            rain_pct  = daily["precipitation_probability_max"][i]
            rain_mm   = daily["precipitation_sum"][i] or 0
            day_desc  = WMO.get(wc, "unknown")

            line = f"{label}: {day_desc}, {tmin}–{tmax}°C, {rain_pct}% chance of rain"
            if rain_mm > 0.1:
                line += f" ({rain_mm:.1f}mm expected)"
            parts.append(line)

            if i + 1 >= forecast_days + 1:
                break

        return ". ".join(parts)

    except Exception as e:
        return f"Couldn't get weather for {city}: {e}"
