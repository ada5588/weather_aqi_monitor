# Weather and Air Quality

A daily pipeline that fetches hourly weather and air quality data for multiple cities, cleans and loads it into PostgreSQL, calculates activity alerts, generates an HTML report for a selected city, and emails that report.

## What it does

1. **Extract** — pull city locations from Postgres and fetch weather + AQI data from the Open-Meteo API
2. **Unpack & clean** — keep today's `America/New_York` hours and validate value ranges
3. **Load** — merge weather + AQI and write to the `weather_aqi_hourly` table
4. **Report** — generate an HTML report with a temperature/precipitation chart and activity suggestions for the selected city (alerts are computed here, not during load)
5. **Email** — send the HTML report via SMTP, with the chart embedded as a CID image so it displays in mail clients



## Project structure

```
├── pipelines/
│   ├── daily_weather_aqi.py  # Extract, clean, and load data
│   └── generate_report.py    # Generate HTML city report
├── config.py               # Table names and timezone
├── connectors/
│   ├── api_client.py       # Open-Meteo API client
│   └── db_client.py        # Postgres connections (read + write)
├── jobs/
│   ├── extract.py          # Fetch data from API and database
│   ├── clean.py            # Clean data and calculate alerts
│   ├── load.py             # Load data into Postgres
│   ├── report.py           # Generate HTML city report
│   └── email.py            # Send the HTML report by email
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

**Report city** — `REPORT_CITY_NAME` is the `city_data.city_name` value used when emailing a report (for example `Newport`).

**Email (SMTP)** — used by `jobs/email.py`:


| Variable        | Purpose                                                 |
| --------------- | ------------------------------------------------------- |
| `SMTP_HOST`     | Mail server (default in the template: `smtp.gmail.com`) |
| `SMTP_PORT`     | Port (template: `587` for STARTTLS)                     |
| `SMTP_USER`     | From address / SMTP login                               |
| `SMTP_PASSWORD` | SMTP password                                           |
| `EMAIL_TO`      | Recipient address                                       |


For Gmail, `SMTP_PASSWORD` must be an [App Password](https://support.google.com/accounts/answer/185833), not your normal Google password. 2-Step Verification has to be on for that account.

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



### Generate a city report

```bash
python -m pipelines.generate_report "Newport"
```

Reports are saved to `reports/` as HTML files.

### Email a city report

After an HTML report exists, send it with `jobs.email.send_report_email`:

```python
from jobs.email import send_report_email

send_report_email("reports/sample/newport_2026-08-12.html", "Newport")
```

The function reads SMTP settings from `.env`. Email clients often block inline `data:` images, so the chart is converted from a base64 data URI to a CID (Content-ID) attachment before sending.

[Email report sample](/reports/sample/email.png)

## Data flow

```
city_data (Postgres)
    ↓
Open-Meteo API → weather + AQI hourly data
    ↓
clean & merge → weather_aqi_hourly (Postgres)
    ↓
calculate alerts → HTML report
    ↓
email (SMTP, CID-embedded chart)
```



## Notes

- All times use the `America/New_York` timezone
- The daily load keeps only the current New York calendar day; it does not calculate alerts
- Alerts are calculated for daytime hours (7am–8pm) when generating a report and are not stored in the database
- Table names are configured in `config.py`
- Copy `.env.template` to `.env` and fill in secrets; `.env` is gitignored
- Gmail sending uses `SMTP_*` and `EMAIL_TO` in `.env` (App Password, not your account password)

