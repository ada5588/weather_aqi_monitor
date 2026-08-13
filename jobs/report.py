import base64
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader
from plotly.subplots import make_subplots

from sqlalchemy import text

from connectors.db_client import get_sqlalchemy_engine
from config import CITY_DATA_TABLE, WEATHER_AQI_HOURLY_TABLE
from jobs.clean import calculate_alert_data

REPORT_TIMEZONE = "America/New_York"
CATEGORY_LABELS = {
	"positive": "Good to go",
	"caution": "Caution",
	"warning": "Warnings",
}
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "templates"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"


def _parse_timestamps(series):
	timestamps = pd.to_datetime(series)
	if timestamps.dt.tz is None:
		return timestamps.dt.tz_localize(REPORT_TIMEZONE)
	return timestamps.dt.tz_convert(REPORT_TIMEZONE)


def fetch_city_hourly_data(city_name):
	engine = get_sqlalchemy_engine("readonly")
	query = text(f"""
		SELECT
			c.city_name,
			w.city_id,
			w.timestamp,
			w.us_aqi,
			w.temperature,
			w.apparent_temperature,
			w.relative_humidity,
			w.rain,
			w.precipitation_probability,
			w.uv_index
		FROM {WEATHER_AQI_HOURLY_TABLE} w
		JOIN {CITY_DATA_TABLE} c ON w.city_id = c.city_id
		WHERE c.city_name = :city_name
			AND w.timestamp >= (
				date_trunc('day', CURRENT_TIMESTAMP AT TIME ZONE '{REPORT_TIMEZONE}')
				AT TIME ZONE '{REPORT_TIMEZONE}'
			)
			AND w.timestamp < (
				(date_trunc('day', CURRENT_TIMESTAMP AT TIME ZONE '{REPORT_TIMEZONE}')
					+ INTERVAL '1 day')
				AT TIME ZONE '{REPORT_TIMEZONE}'
			)
		ORDER BY w.timestamp
	""")

	try:
		with engine.connect() as conn:
			hourly_data = pd.read_sql(query, conn, params={"city_name": city_name})
	finally:
		engine.dispose()

	if hourly_data.empty:
		raise ValueError(f"No weather data found for city '{city_name}' today.")

	hourly_data["timestamp"] = _parse_timestamps(hourly_data["timestamp"]).dt.floor("h")
	return hourly_data


def format_time(timestamp):
	hour = int(timestamp.strftime("%I"))
	minute = timestamp.strftime("%M")
	return f"{hour}:{minute} {timestamp.strftime('%p')}"


def format_period(start_time, end_time):
	return f"{format_time(start_time)}–{format_time(end_time)}"


def build_summary(alerts):
	if alerts.empty:
		return "No daytime activity suggestions for today."

	parts = {}
	for _, alert in alerts.iterrows():
		period = format_period(alert["start_time"], alert["end_time"])
		if alert['message'] not in parts:
			parts[alert['message']] = []
		parts[alert['message']].append(period)
		

	return '\n'.join(
		f'{k}: {', '.join(v)}'
		for k, v in parts.items()
	)


def build_alert_sections(alerts):
	sections = []
	for category, title in CATEGORY_LABELS.items():
		category_alerts = alerts[alerts["category"] == category].sort_values("start_time")
		if category_alerts.empty:
			continue

		sections.append({
			"title": title,
			"alerts": [
				{
					"message": row["message"],
					"period": format_period(row["start_time"], row["end_time"]),
				}
				for _, row in category_alerts.iterrows()
			],
		})
	return sections


def _build_chart_frame(hourly_data):
	today = pd.Timestamp.now(tz=REPORT_TIMEZONE).normalize()
	chart_frame = pd.DataFrame({
		"timestamp": pd.date_range(today, periods=24, freq="h"),
	})
	chart_frame = chart_frame.merge(
		hourly_data[["timestamp", "temperature", "precipitation_probability"]],
		on="timestamp",
		how="left",
	)
	chart_frame["hour_label"] = chart_frame["timestamp"].dt.strftime("%H")
	return chart_frame


def build_chart_base64(hourly_data):
	chart_frame = _build_chart_frame(hourly_data)

	figure = make_subplots(specs=[[{"secondary_y": True}]])
	
	figure.add_trace(
		go.Scatter(
			x=chart_frame["hour_label"],
			y=chart_frame["precipitation_probability"],
			name="Precipitation probability (%)",
			mode="lines+markers",
			connectgaps=False,
		),
		secondary_y=False,
	)
	
	figure.add_trace(
		go.Scatter(
			x=chart_frame["hour_label"],
			y=chart_frame["temperature"],
			name="Temperature (°C)",
			mode="lines+markers",
			connectgaps=False,
		),
		secondary_y=True,
	)

	
	figure.update_layout(
		title="Temperature and precipitation probability (0:00–23:00)",
		xaxis_title="Hour",
		template="plotly_white",
		height=420,
		margin=dict(l=40, r=40, t=60, b=40),
		legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
		yaxis=dict(
        showgrid=True,
        gridcolor='LightBlue',
        gridwidth=1.5,
        griddash='dot'
    ),
    
		yaxis2=dict(
        showgrid=True,
        gridcolor='lightcoral',
        gridwidth=1,
        griddash='dashdot',
        overlaying='y',  # Keeps them positioned over the same plot space
        side='right'     # Puts the secondary scale numbers on the right
    ),
	)
	
	figure.update_yaxes(title_text="Precipitation (%)", secondary_y=False, range=[0, 100])
	figure.update_yaxes(title_text="Temperature (°C)", secondary_y=True)

	image_bytes = figure.to_image(format="png", scale=2)
	return base64.b64encode(image_bytes).decode("utf-8")


def render_report_html(city_name, hourly_data, alerts):
	environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
	template = environment.get_template("report.html")
	return template.render(
		city_name=city_name,
		chart_base64=build_chart_base64(hourly_data),
		summary=build_summary(alerts),
		alert_sections=build_alert_sections(alerts),
	)


def _sanitize_filename(value):
	return re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower())


def _default_output_paths(city_name):
	report_date = pd.Timestamp.now(tz=REPORT_TIMEZONE).strftime("%Y-%m-%d")
	filename = f"{_sanitize_filename(city_name)}_{report_date}"
	DEFAULT_REPORT_DIR.mkdir(exist_ok=True)
	return DEFAULT_REPORT_DIR / f"{filename}.html"


def generate_report(city_name, output_path=None):
	hourly_data = fetch_city_hourly_data(city_name)
	# city_name = hourly_data["city_name"].iloc[0]
	alerts = calculate_alert_data(hourly_data)
	html_content = render_report_html(city_name, hourly_data, alerts)

	html_path = Path(output_path) if output_path else _default_output_paths(city_name)
	if output_path and html_path.suffix.lower() != ".html":
		html_path = html_path.with_suffix(".html")

	html_path.write_text(html_content, encoding="utf-8")
	return html_path
