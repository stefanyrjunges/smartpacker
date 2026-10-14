import os
import logging
from datetime import date
import requests

logger = logging.getLogger(__name__)

# Getting weather from WeatherAPI and handling possible errors
# The API key is read from an env variable so it's not hard-coded

def get_weather(destination, start_date, end_date):
    api_key = os.environ.get("WEATHER_API_KEY")

    if not api_key:
        logger.error("WEATHER_API_KEY is not set")
        return {"error": "Weather service is not configured."}

    # Handling errors for date limits in the API
    days_ahead = (end_date - date.today()).days + 1

    if days_ahead < 1:
        return {"error": "Weather is only available for upcoming trips."}

    if days_ahead > 14:
        return {"error": "Weather is only available up to 14 days ahead."}

    url = "https://api.weatherapi.com/v1/forecast.json"

    params = {
        "key": api_key,
        "q": destination,
        "days": days_ahead
    }

    # Handle network problems like timeouts or bad status codes
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        status = e.response.status_code if e.response is not None else "no response"
        body = e.response.text if e.response is not None else ""
        logger.error(
            "Weather request failed for %s (%s to %s): %s: %s (HTTP %s) %s",
            destination, start_date, end_date, type(e).__name__, e, status, body
        )
        return {"error": "Unable to retrieve weather data. Try again in a moment."}

    location = data.get("location")
    forecast_days = data.get("forecast", {}).get("forecastday", [])

    if not location or not forecast_days:
        logger.error("Weather response had no forecast for destination: %s", destination)
        return {"error": "Weather data is not available for this destination."}

    # Keep only the days inside the trip's dates
    start_text = start_date.isoformat()
    end_text = end_date.isoformat()
    trip_days = [d for d in forecast_days if start_text <= d["date"] <= end_text]

    if not trip_days:
        return {"error": "Weather data is not available for these dates."}

    min_temperature = min(d["day"]["mintemp_c"] for d in trip_days)
    max_temperature = max(d["day"]["maxtemp_c"] for d in trip_days)
    total_precipitation = round(sum(d["day"]["totalprecip_mm"] for d in trip_days), 1)
    rain_expected = total_precipitation > 0

    return {
        "destination": location["name"],
        "country": location["country"],
        "min_temperature": min_temperature,
        "max_temperature": max_temperature,
        "total_precipitation": total_precipitation,
        "rain_expected": rain_expected
    }
