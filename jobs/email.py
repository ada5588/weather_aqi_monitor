import base64
import os
import re
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CHART_DATA_URI_PATTERN = re.compile(
	r'src="data:image/png;base64,([^"]+)"',
)
CHART_CONTENT_ID = "weather_chart"


def embed_chart_for_email(html_content):
	"""Replace data-URI chart with a CID reference for email clients."""
	match = CHART_DATA_URI_PATTERN.search(html_content)
	if not match:
		return html_content, None

	chart_base64 = match.group(1)
	html_content = html_content.replace(
		f"data:image/png;base64,{chart_base64}",
		f"cid:{CHART_CONTENT_ID}",
	)
	return html_content, base64.b64decode(chart_base64)


def send_report_email(html_path, city_name):
	smtp_host = os.getenv("SMTP_HOST")
	smtp_port = int(os.getenv("SMTP_PORT", 587))
	smtp_user = os.getenv("SMTP_USER")
	smtp_password = os.getenv("SMTP_PASSWORD")
	email_to = os.getenv("EMAIL_TO")

	if not all([smtp_host, smtp_user, smtp_password, email_to]):
		raise ValueError("Missing SMTP settings in .env")

	html_content = Path(html_path).read_text(encoding="utf-8")
	html_content, chart_bytes = embed_chart_for_email(html_content)

	message = MIMEMultipart("related")
	message["Subject"] = f"Today's weather in {city_name}"
	message["From"] = smtp_user
	message["To"] = email_to
	message.attach(MIMEText(html_content, "html"))

	if chart_bytes:
		chart_image = MIMEImage(chart_bytes, _subtype="png")
		chart_image.add_header("Content-ID", f"<{CHART_CONTENT_ID}>")
		chart_image.add_header("Content-Disposition", "inline", filename="chart.png")
		message.attach(chart_image)

	with smtplib.SMTP(smtp_host, smtp_port) as server:
		server.starttls()
		server.login(smtp_user, smtp_password)
		server.send_message(message)
