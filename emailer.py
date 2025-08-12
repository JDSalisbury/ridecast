# emailer.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM
from logger import logger


def send_email(to_address: str, subject: str, html_body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = to_address
        msg["Subject"] = subject

        part = MIMEText(html_body, "html")
        msg.attach(part)

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {to_address}")
        return True

    except Exception as e:
        logger.error(f"Error sending email to {to_address}: {e}")
        return False
