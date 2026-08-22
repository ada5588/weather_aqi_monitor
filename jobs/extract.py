import os
from dotenv import load_dotenv
import pandas as pd
from connectors.api_client import get_openmeteo_client
from connectors.db_client import get_postgres_connection
from connectors.db_client import get_sqlalchemy_engine
from config import CITY_DATA_TABLE

load_dotenv()


def get_city_data():
    engine = get_sqlalchemy_engine()
    try:
        return pd.read_sql(
            f"SELECT city_id, latitude, longitude FROM {CITY_DATA_TABLE}",
            engine,
        )
    finally:
        engine.dispose()


def prepare_params_for_weather_api(city_data):
	url = os.getenv("WEATHER_API_URL")
	params = {
		"latitude": city_data["latitude"].tolist(),
		"longitude": city_data["longitude"].tolist(),
		"hourly": os.getenv("WEATHER_DATA_FIELDS").split(","),
		"models": os.getenv("WEATHER_MODEL").split(","),
		"forecast_days": os.getenv("WEATHER_FORECAST_DAYS"),
	}
	return url, params


def get_weather_data(city_data):
	url, params = prepare_params_for_weather_api(city_data)
	openmeteo = get_openmeteo_client()
	try:
		responses = openmeteo.weather_api(url, params=params)
	except Exception as e:
		print(f"Failed to fetch weather data: {e}")
		return None

	return {
		city_id: responses[i]
		for i, city_id in enumerate(city_data["city_id"])
	}


def prepare_params_for_aqi_api(city_data):
	url = os.getenv("AQI_API_URL")
	params = {
		"latitude": city_data["latitude"].tolist(),
		"longitude": city_data["longitude"].tolist(),
		"hourly": os.getenv("AQI_DATA_FIELDS"),
		"forecast_days": os.getenv("AQI_FORECAST_DAYS"),
	}
	return url, params

def get_aqi_data(city_data):
	openmeteo = get_openmeteo_client()
	url, params = prepare_params_for_aqi_api(city_data)
	try:
		responses = openmeteo.weather_api(url, params=params)
	except Exception as e:
		print(f"Failed to fetch AQI data: {e}")
		return None

	return {
		city_id: responses[i]
		for i, city_id in enumerate(city_data["city_id"])
	}
	
