from config import WEATHER_AQI_HOURLY_TABLE
from connectors.db_client import get_sqlalchemy_engine
from config import WEATHER_AQI_HOURLY_TABLE

def load_weather_aqi_data(combined_dataframe):
    engine = get_sqlalchemy_engine("write")
    combined_dataframe.to_sql(
        WEATHER_AQI_HOURLY_TABLE,
        engine,
        if_exists="append",
        index=False,
    )
    return len(combined_dataframe)