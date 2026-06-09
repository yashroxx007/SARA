import requests

def get_weather(city="Bangalore"):
    url = f"https://wttr.in/{city}?format=j1"
    r = requests.get(url, timeout=5)
    data = r.json()
    
    current = data["current_condition"][0]
    temp = current["temp_C"]
    feels_like = current["FeelsLikeC"]
    description = current["weatherDesc"][0]["value"]
    humidity = current["humidity"]
    
    return f"{description}, {temp} degrees, feels like {feels_like}, humidity {humidity} percent"