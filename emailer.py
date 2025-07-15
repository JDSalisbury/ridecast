# emailer.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM


def send_email(to_address: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = to_address
        msg["Subject"] = subject

        html_body = f"""
            <html>
                <body>
                    <pre style="font-family: monospace; font-size: 14px;">{body}</pre>
                </body>
            </html>
        """
        part = MIMEText(html_body, "html")
        msg.attach(part)

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL] Sent to {to_address}")
        return True

    except Exception as e:
        print(f"[EMAIL] Error sending to {to_address}: {e}")
        return False
