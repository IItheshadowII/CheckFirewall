from email.message import EmailMessage
import aiosmtplib
from config import settings

async def send_alert_email(hostname: str, ip: str, last_seen: str):
    message = EmailMessage()
    message["From"] = settings.ALERT_SENDER_EMAIL
    message["To"] = settings.ALERT_RECIPIENT_EMAIL
    message["Subject"] = f"CRITICAL: Firewall Alert for {hostname}"
    
    body = f"""
    ALERT: Windows Firewall Monitor
    
    The agent on host '{hostname}' ({ip}) has reported an issue or has gone silent.
    
    Last Seen: {last_seen}
    
    Please check the host immediately.
    """
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOSTNAME,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True
        )
        print(f"Alert email sent for {hostname}")
    except Exception as e:
        print(f"Failed to send email: {e}")
