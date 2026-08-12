from jobs.extract import *
from jobs.clean import *
from jobs.load import load_weather_aqi_data
from jobs.report import generate_report
import pandas as pd

def main():
	city_data = get_city_data()
	weather_data = get_weather_data(city_data)
	weather_dataframe = unpack_response(weather_data)
	aqi_data = get_aqi_data(city_data)
	aqi_dataframe = unpack_response(aqi_data, response_type='aqi')
	aqi_dataframe = clean_aqi_data(aqi_dataframe)
	weather_dataframe = clean_weather_data(weather_dataframe)

	# aqi_dataframe.to_csv('aqi_dataframe.csv', index=False)
	# weather_dataframe.to_csv('weather_dataframe.csv', index=False)

	combined = pd.merge(aqi_dataframe, weather_dataframe, on=['timestamp','city_id'], how='inner')
	rows_loaded = load_weather_aqi_data(combined)
	print(f"Loaded {rows_loaded} rows into database")
	alerts = calculate_alert_data(combined)
	# alerts.to_csv('alerts.csv', index=False)

	html_path = generate_report('Highland Heights')
	print(f"HTML report: {html_path}")


if __name__ == "__main__":
	main()