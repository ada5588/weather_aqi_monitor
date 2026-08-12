import pandas as pd
from jobs.extract import get_city_data, get_weather_data, get_aqi_data
from jobs.clean import unpack_response, clean_weather_data, clean_aqi_data
from jobs.load import load_weather_aqi_data


def main():
    city_data = get_city_data()
    weather_data = get_weather_data(city_data)
    weather_dataframe = unpack_response(weather_data)
    weather_dataframe = clean_weather_data(weather_dataframe)
    aqi_data = get_aqi_data(city_data)
    aqi_dataframe = unpack_response(aqi_data, response_type='aqi')
    aqi_dataframe = clean_aqi_data(aqi_dataframe)

    rows_loaded = load_weather_aqi_data(weather_dataframe, aqi_dataframe)
    print(f"Loaded {rows_loaded} rows into database")
    
if __name__ == "__main__":
	main()