import pandas as pd

def unpack_response(response, response_type='weather'):
	# Process hourly data. The order of variables needs to be the same as requested.
	cities = list(response.keys())
	
	combined_dataframe = []
	for i in cities:
		hourly = response[i].Hourly()

		hourly_data = {
			"timestamp": pd.date_range(
				start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
				end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
				freq=pd.Timedelta(seconds=hourly.Interval()),
				inclusive="left",
			).tz_convert("America/New_York")
		}
		if response_type == 'weather':
			hourly_data["temperature"] = hourly.Variables(0).ValuesAsNumpy()
			hourly_data["relative_humidity"] = hourly.Variables(1).ValuesAsNumpy()
			hourly_data["apparent_temperature"] = hourly.Variables(2).ValuesAsNumpy()
			hourly_data["rain"] = hourly.Variables(3).ValuesAsNumpy()
			hourly_data["precipitation_probability"] = hourly.Variables(4).ValuesAsNumpy()
			hourly_data["uv_index"] = hourly.Variables(5).ValuesAsNumpy()
		elif response_type == 'aqi':
			hourly_data["us_aqi"] = hourly.Variables(0).ValuesAsNumpy()

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

def clean_aqi_data(hourly_dataframe):
	# check us_aqi
	hourly_dataframe["us_aqi"] = hourly_dataframe["us_aqi"].where(hourly_dataframe["us_aqi"].between(0.0, 500.0))

	return hourly_dataframe


ALERT_DEFINITIONS = [
	{
		"code": "outdoor_workout_good",
		"category": "positive",
		"message": "Outdoor workout is good",
		"condition": lambda df: (
			(df["apparent_temperature"] < 28)
			& (df["us_aqi"] <= 50)
			& (df["rain"] < 1)
		),
	},
	{
		"code": "open_window",
		"category": "positive",
		"message": "Open the window(good for outdoor workout too)",
		"condition": lambda df: (
			(df["temperature"] < 30)
			& (df["us_aqi"] <= 50)
			& (df["relative_humidity"] < 60)
		),
	},
	{
		"code": "bring_umbrella",
		"category": "caution",
		"message": "Bring an umbrella",
		"condition": lambda df: df["precipitation_probability"] > 50,
	},
	{
		"code": "stay_indoors_aqi",
		"category": "warning",
		"message": "Stay indoors (poor air quality)",
		"condition": lambda df: df["us_aqi"] > 100,
	},
	{
		"code": "sun_protection",
		"category": "caution",
		"message": "Use sun protection",
		"condition": lambda df: df["uv_index"] > 3,
	},
	{
		"code": "stay_indoors_uv",
		"category": "warning",
		"message": "Stay indoors (very high UV)",
		"condition": lambda df: df["uv_index"] > 8,
	},
]


ALERT_COLUMNS = [
	"city_id", "alert_date", "code", "category", "message", "start_time", "end_time"
]


def _filter_daytime_hours(dataframe):
	daytime_hours = dataframe["timestamp"].dt.hour
	return dataframe.loc[(daytime_hours >= 7) & (daytime_hours <= 20)].copy()


def _empty_alert_dataframe():
	return pd.DataFrame(columns=ALERT_COLUMNS)


def _matches_to_periods(matches):
	if matches.empty:
		return matches

	matches = matches.sort_values(["city_id", "code", "timestamp"])
	previous_timestamp = matches.groupby(["city_id", "code"])["timestamp"].shift()
	matches["period_id"] = (
		previous_timestamp.isna()
		| (matches["timestamp"] - previous_timestamp > pd.Timedelta(hours=1))
	).cumsum()

	periods = matches.groupby(["city_id", "code", "period_id"], as_index=False).agg(
		start_time=("timestamp", "min"),
		end_time=("timestamp", "max"),
	)
	periods["end_time"] = periods["end_time"] + pd.Timedelta(hours=1)
	periods["alert_date"] = periods["start_time"].dt.normalize().dt.date
	return periods


def calculate_alert_data(combined_dataframe):
	daytime_data = _filter_daytime_hours(combined_dataframe)
	if daytime_data.empty:
		return _empty_alert_dataframe()

	for alert in ALERT_DEFINITIONS:
		daytime_data[alert["code"]] = alert["condition"](daytime_data)

	alert_codes = [alert["code"] for alert in ALERT_DEFINITIONS]
	matches = daytime_data.melt(
		id_vars=["city_id", "timestamp"],
		value_vars=alert_codes,
		var_name="code",
		value_name="active",
	)
	matches = matches.loc[matches["active"], ["city_id", "timestamp", "code"]]

	periods = _matches_to_periods(matches)
	if periods.empty:
		return _empty_alert_dataframe()

	metadata = pd.DataFrame(ALERT_DEFINITIONS)[["code", "category", "message"]]
	return periods.merge(metadata, on="code").sort_values(
		["city_id", "alert_date", "code", "start_time"]
	).reset_index(drop=True)[ALERT_COLUMNS]
