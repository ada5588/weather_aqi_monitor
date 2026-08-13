from jobs.extract import get_city_data, get_weather_data, get_aqi_data
from jobs.clean import unpack_response, clean_weather_data, clean_aqi_data
from jobs.load import load_weather_aqi_data


def run_daily_load():
	city_data = get_city_data()
	weather_data = get_weather_data(city_data)
	weather_dataframe = clean_weather_data(unpack_response(weather_data))
	aqi_data = get_aqi_data(city_data)
	aqi_dataframe = clean_aqi_data(unpack_response(aqi_data, response_type="aqi"))
	return load_weather_aqi_data(weather_dataframe, aqi_dataframe)


def main():
	rows_loaded = run_daily_load()
	print(f"Loaded {rows_loaded} rows into database")


if __name__ == "__main__":
	main()
