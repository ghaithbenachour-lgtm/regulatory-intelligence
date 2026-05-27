import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.app.config import settings


class EmailService:
    def send_digest(self, to_email: str, subject: str, body_plain: str, body_html: str) -> None:
        if not settings.gmail_address or not settings.gmail_app_password:
            raise RuntimeError(
                "GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env "
                "(use a Google App Password)."
            )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.gmail_address
        msg["To"] = to_email

        footer_plain = (
            "\n\n---\nAutomated daily regulatory digest (official sources only).\nReply is not monitored."
        )
        footer_html = (
            "<hr><p><small>Automated daily regulatory digest (official sources only). "
            "Reply is not monitored.</small></p>"
        )

        msg.attach(MIMEText(body_plain + footer_plain, "plain", "utf-8"))
        msg.attach(MIMEText(body_html + footer_html, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as smtp:
            smtp.login(settings.gmail_address, settings.gmail_app_password)
            smtp.sendmail(settings.gmail_address, [to_email], msg.as_string())
