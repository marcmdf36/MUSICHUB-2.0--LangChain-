import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from agent.config import SMTP_EMAIL, SMTP_PASSWORD, RECIPIENTS


def send_email(subject: str, html_body: str, recipients: list[str] = None) -> bool:
    """Envía el email individualmente a cada destinatario."""
    recipients = recipients or RECIPIENTS

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)

            for recipient in recipients:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = SMTP_EMAIL
                msg["To"] = recipient
                msg.attach(MIMEText(html_body, "html"))

                server.sendmail(SMTP_EMAIL, [recipient], msg.as_string())

        return True
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False