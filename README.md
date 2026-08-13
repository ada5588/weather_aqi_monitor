# Weather and Air Quality

A daily pipeline that fetches hourly weather and air quality data for multiple cities, cleans and loads it into PostgreSQL, calculates activity alerts, and generates an HTML report for a selected city.

## What it does

1. **Extract** — pull city locations from Postgres and fetch weather + AQI data from the Open-Meteo API
2. **Unpack & clean** — keep today's `America/New_York` hours and validate value ranges
3. **Load** — merge weather + AQI and write to the `weather_aqi_hourly` table
4. **Report** — generate an HTML report with a temperature/precipitation chart and activity suggestions for the selected city (alerts are computed here, not during load)

## Project structure

```
├── pipelines/
│   ├── daily_weather_aqi.py  # Extract, unpack, clean, and load (`run_daily_load`)
│   ├── generate_report.py    # Generate HTML city report
│   └── morning_job.py        # Optional: load + report + email
├── config.py               # Table names and timezone
├── connectors/
│   ├── api_client.py       # Open-Meteo API client
│   └── db_client.py        # Postgres connections (read + write)
├── jobs/
│   ├── extract.py          # Fetch data from API and database
│   ├── clean.py            # Clean data and calculate alerts
│   ├── load.py             # Load data into Postgres
│   └── report.py           # Generate HTML city report
├── templates/
│   └── report.html         # HTML report template
├── scripts/
│   └── test_db_connection.py
├── reports/                # Generated HTML reports
└── .env.template           # Environment variable template
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.template .env
```

Fill in your Postgres credentials in `.env`. The project uses two database users:

- **readonly** — for queries (extract, report)
- **write** — for loading data

### 3. Set up the database

Create the hourly data table in Postgres:

```sql
CREATE TABLE weather_aqi_hourly (
    city_id INT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    us_aqi DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    apparent_temperature DOUBLE PRECISION,
    relative_humidity DOUBLE PRECISION,
    rain DOUBLE PRECISION,
    precipitation_probability DOUBLE PRECISION,
    uv_index DOUBLE PRECISION,
    PRIMARY KEY (city_id, timestamp)
);
```

You also need a `city_data` table with `city_id`, `city_name`, `latitude`, and `longitude`.

### 4. Test the database connection

```bash
python scripts/test_db_connection.py
```

## Usage

### Load daily weather and AQI data

```bash
python -m pipelines.daily_weather_aqi
```

This runs `run_daily_load()`: fetch city coordinates, pull weather and AQI, unpack today's New York hours, clean ranges, merge, and insert into `weather_aqi_hourly`. It prints how many rows were loaded. Other pipelines (such as `morning_job`) can import and call `run_daily_load()` instead of duplicating those steps.

### Generate a city report

```bash
python -m pipelines.generate_report "Highland Heights"
```

Reports are saved to `reports/` as HTML files.

## Data flow

```
city_data (Postgres)
    ↓
Open-Meteo API → weather + AQI hourly data
    ↓
unpack (today in America/New_York) → clean ranges → merge
    ↓
weather_aqi_hourly (Postgres)
    ↓
calculate alerts → HTML report
```

## Notes

- All times use the `America/New_York` timezone
- The daily load keeps only the current New York calendar day; it does not calculate alerts
- Alerts are calculated for daytime hours (7am–8pm) when generating a report and are not stored in the database
- Table names are configured in `config.py`
