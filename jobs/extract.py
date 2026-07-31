from connectors.api_client import get_openmeteo_client #import path problem


def get_weather_data(latitude, longitude):
    import logging
    logging.basicConfig(filename="weather.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s")
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
	"latitude": latitude,
	"longitude": longitude,
	"hourly": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "rain", "precipitation_probability", "uv_index"],
	"models": ["ncep_gfs_seamless"],
	"forecast_days": 2,
    }
    
    openmeteo = get_openmeteo_client()
    try:
        responses = openmeteo.weather_api(url, params = params)
    except Exception as e:
        logging.exception(f"Failed to fetch weather data: {e}")
        return None
    
    return responses[0]

