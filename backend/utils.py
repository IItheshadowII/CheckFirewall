from email.message import EmailMessage
from typing import Iterable

import aiosmtplib

from config import settings


async def send_alert_email(hosts: Iterable["models.Host"], manual: bool = False) -> None:
        """Send a single aggregated alert email for all problematic hosts.

        Each host should be an instance of models.Host with firewall_status,
        hostname, ip_address and last_seen populated.
        """

        hosts = list(hosts)
        if not hosts:
                return

        # Build plain-text fallback
        lines = [
                "FirewallWatch - Alert Report",
                "",
                f"Total problematic hosts: {len(hosts)}",
                "",
        ]
        for h in hosts:
                status = "AT RISK" if not getattr(h, "firewall_status", True) else "SILENT"
                lines.append(f"- {h.hostname} ({h.ip_address}) - {status} - last seen {h.last_seen}")

        plain_body = "\n".join(lines)

        # Build pretty HTML body
        rows = []
        for h in hosts:
                is_risky = not getattr(h, "firewall_status", True)
                status_label = "At Risk" if is_risky else "Silent"
                icon = "&#128308;" if is_risky else "&#9888;"  # red circle / warning
                color = "#f97373" if is_risky else "#facc15"   # red / amber
                rows.append(
                        f"""
                        <tr>
                            <td style='padding:8px 12px;border-bottom:1px solid #1f2937;'>{h.hostname}</td>
                            <td style='padding:8px 12px;border-bottom:1px solid #1f2937;font-family:monospace;'>{h.ip_address}</td>
                            <td style='padding:8px 12px;border-bottom:1px solid #1f2937;color:{color};font-weight:600;'>
                                <span style='margin-right:4px'>{icon}</span>{status_label}
                            </td>
                            <td style='padding:8px 12px;border-bottom:1px solid #1f2937;font-size:12px;color:#9ca3af;'>
                                {h.last_seen}
                            </td>
                        </tr>
                        """
                )

        reason = "Manual alert trigger" if manual else "Automatic alert based on monitoring rules"

        html_body = f"""
        <html>
            <body style='background-color:#030712;color:#e5e7eb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:24px;'>
                <div style='max-width:640px;margin:0 auto;background:#020617;border-radius:16px;border:1px solid #1f2937;overflow:hidden;'>
                    <div style='padding:16px 20px;border-bottom:1px solid #1f2937;background:linear-gradient(135deg,#4f46e5,#0f172a);'>
                        <h1 style='margin:0;font-size:18px;font-weight:700;color:white;'>FirewallWatch Alerts</h1>
                        <p style='margin:4px 0 0;font-size:12px;color:#e5e7eb;'>{reason}</p>
                    </div>
                    <div style='padding:20px;'>
                        <p style='margin:0 0 12px;font-size:14px;'>Hola,</p>
                        <p style='margin:0 0 16px;font-size:14px;'>Se detectaron los siguientes hosts con posibles problemas de firewall o sin reportar actividad:</p>
                        <table style='width:100%;border-collapse:collapse;font-size:13px;background:#020617;border-radius:12px;overflow:hidden;'>
                            <thead style='background:#111827;text-align:left;'>
                                <tr>
                                    <th style='padding:8px 12px;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;'>Host</th>
                                    <th style='padding:8px 12px;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;'>IP</th>
                                    <th style='padding:8px 12px;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;'>Estado</th>
                                    <th style='padding:8px 12px;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;'>Último heartbeat</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(rows)}
                            </tbody>
                        </table>
                        <p style='margin:16px 0 0;font-size:12px;color:#9ca3af;'>
                            Consejo: podés marcar hosts conocidos en el dashboard para evitar alertas futuras mientras estén marcados como conocidos.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

        message = EmailMessage()
        message["From"] = settings.ALERT_SENDER_EMAIL
        message["To"] = settings.ALERT_RECIPIENT_EMAIL
        message["Subject"] = f"FirewallWatch - {len(hosts)} host(s) en alerta"
        message.set_content(plain_body)
        message.add_alternative(html_body, subtype="html")

        try:
                await aiosmtplib.send(
                        message,
                        hostname=settings.SMTP_HOSTNAME,
                        port=settings.SMTP_PORT,
                        username=settings.SMTP_USERNAME,
                        password=settings.SMTP_PASSWORD,
                        start_tls=True,
                )
                print(f"Alert email sent for {len(hosts)} host(s)")
        except Exception as e:
                print(f"Failed to send email: {e}")
