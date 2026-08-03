import pandas as pd
import numpy as np

def unpack_weather_response(weather_data):
	# Process hourly data. The order of variables needs to be the same as requested.
	cities = list(weather_data.keys())
	
	combined_dataframe = []
	for i in cities:
		hourly = weather_data[i].Hourly()

		hourly_data = {
			"timestamp": pd.date_range(
				start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
				end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
				freq=pd.Timedelta(seconds=hourly.Interval()),
				inclusive="left",
			).tz_convert("America/New_York")
		}
		hourly_data["temperature"] = hourly.Variables(0).ValuesAsNumpy()
		hourly_data["relative_humidity"] = hourly.Variables(1).ValuesAsNumpy()
		hourly_data["apparent_temperature"] = hourly.Variables(2).ValuesAsNumpy()
		hourly_data["rain"] = hourly.Variables(3).ValuesAsNumpy()
		hourly_data["precipitation_probability"] = hourly.Variables(4).ValuesAsNumpy()
		hourly_data["uv_index"] = hourly.Variables(5).ValuesAsNumpy()

		hourly_dataframe = pd.DataFrame(data=hourly_data)

		# Keep only today's America/New_York date
		today = pd.Timestamp.now(tz="America/New_York").normalize()
		hourly_data = hourly_dataframe[hourly_dataframe["timestamp"].dt.normalize() == today]
		hourly_data['city_id'] = i
		combined_dataframe.append(hourly_data)
	
	return pd.concat(combined_dataframe, ignore_index=True)


def clean_weather_data(hourly_dataframe):
	# check temperature
	hourly_dataframe["temperature"] = hourly_dataframe["temperature"].where(hourly_dataframe["temperature"].between(-20.0, 40.0))

	# check relative humidity
	hourly_dataframe["relative_humidity"] = hourly_dataframe["relative_humidity"].where(hourly_dataframe["relative_humidity"].between(0.0, 100.0))

	# check apparent temperature
	hourly_dataframe["apparent_temperature"] = hourly_dataframe["apparent_temperature"].where(hourly_dataframe["apparent_temperature"].between(-20.0, 40.0))

	# check rain
	hourly_dataframe["rain"] = hourly_dataframe["rain"].where(hourly_dataframe["rain"] >= 0.0)

	# check precipitation probability
	hourly_dataframe["precipitation_probability"] = hourly_dataframe["precipitation_probability"].where(hourly_dataframe["precipitation_probability"].between(0.0, 100.0))

	# check uv index
	hourly_dataframe["uv_index"] = hourly_dataframe["uv_index"].where(hourly_dataframe["uv_index"]>=0.0)

	return hourly_dataframe
