import pandas as pd

def clean_weather_response(response):
    # Process hourly data. The order of variables needs to be the same as requested.
	hourly = response.Hourly()
	
	hourly_data = {
		"timestamp": pd.date_range(
			start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
			end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
			freq = pd.Timedelta(seconds = hourly.Interval()),
			inclusive = "left"
		).tz_convert("America/New_York")
	}
	hourly_data["temperature"] = hourly.Variables(0).ValuesAsNumpy()
	hourly_data["relative_humidity"] = hourly.Variables(1).ValuesAsNumpy()
	hourly_data["apparent_temperature"] = hourly.Variables(3).ValuesAsNumpy()
	hourly_data["rain"] = hourly.Variables(3).ValuesAsNumpy()
	hourly_data["precipitation_probability"] = hourly.Variables(4).ValuesAsNumpy()
	hourly_data["uv_index"] = hourly.Variables(5).ValuesAsNumpy()
	
	hourly_dataframe = pd.DataFrame(data = hourly_data)

	# Keep only today's America/New_York date
	today = pd.Timestamp.now(tz="America/New_York").normalize()
	hourly_dataframe = hourly_dataframe[hourly_dataframe["date"].dt.normalize() == today]
    
    return hourly_dataframe