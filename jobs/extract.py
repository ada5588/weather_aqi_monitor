from connectors.api_client import get_openmeteo_client
from connectors.db_client import get_postgres_connection

def get_city_data():
    conn = get_postgres_connection("readonly")
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT city_id, latitude, longitude FROM city_data')
            return {
                city_id: (latitude, longitude)
                for city_id, latitude, longitude in cur.fetchall()
            }
    finally:
        conn.close()

def get_weather_data(city_data):
    import logging
    logging.basicConfig(filename="weather.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s")
    
    cities = list(city_data.keys())
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
	"latitude": [city_data[i][0] for i in cities],
	"longitude": [city_data[i][1] for i in cities],
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
    
    weather_data = {}
    for i in range(len(cities)):
        weather_data[cities[i]] = responses[i]

    return weather_data

