import logging
import requests

logger = logging.getLogger(__name__)

# Get the weather by connecting to open meteo API and handle possible errors

def get_weather(destination, start_date, end_date):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    # Turn the city name into coordinates
    params = {
        "name": destination,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    # Handle network problems like timeout, bad status etc
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        status = e.response.status_code if e.response is not None else "no response"
        logger.error("Geocoding request failed: %s: %s (HTTP %s)", type(e).__name__, e, status)
        return {"error": "Unable to connect to the weather service. Try again in a moment."}

    # Handle a case where the request succeeds but open meteo finds nothing
    if "results" not in data or not data["results"]:
        logger.error("Geocoding returned no results for destination: %s", destination)
        return {"error": "Destination not found. Please check the spelling and try again."}

    # If open meteo found something, take first match and pull coordinates
    location = data["results"][0]
    latitude = location["latitude"]
    longitude = location["longitude"]

    weather_url = "https://api.open-meteo.com/v1/forecast"

    weather_params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "timezone": "auto"
    }

    # Handle network errors or anything that prevents a usable response
    try:
        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()
    except requests.RequestException as e:
        status = e.response.status_code if e.response is not None else "no response"
        body = e.response.text if e.response is not None else ""
        logger.error(
            "Forecast request failed for %s to %s: %s: %s (HTTP %s) %s",
            start_date, end_date, type(e).__name__, e, status, body
        )
        return {"error": "Unable to retrieve weather data. Try again in a moment."}

    # Case where API responds OK but there's no forecast for the dates
    if "daily" not in weather_data:
        logger.error("Forecast response had no 'daily' data for %s to %s", start_date, end_date)
        return {"error": "Weather data is not available for these dates. Open-Meteo only supports forecasts up to 16 days ahead."}

    # Summarise daily data
    daily = weather_data["daily"]

    min_temperature = min(daily["temperature_2m_min"])
    max_temperature = max(daily["temperature_2m_max"])

    total_precipitation = round(
        sum(daily["precipitation_sum"]), 1
    )

    rain_expected = total_precipitation > 0

    return {
        "destination": location["name"],
        "country": location["country"],
        "min_temperature": min_temperature,
        "max_temperature": max_temperature,
        "total_precipitation": total_precipitation,
        "rain_expected": rain_expected
    }
