"""
Email notification service.

Design:
  - Pure send function (_send_blocking) — synchronous, testable.
  - Public entry point (send_new_lead_notification) spawns a daemon thread
    so the HTTP response is never delayed by SMTP I/O.
  - Gracefully no-ops when SMTP_HOST / SMTP_USER / SMTP_PASSWORD are unset.
  - Supports both STARTTLS (port 587, default) and implicit TLS / SMTPS (port 465).
"""

import logging
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


# ── Email builders ────────────────────────────────────────────────────────────

def _fmt_budget(budget: Optional[float], currency_symbol: str) -> str:
    if budget is None or budget <= 0:
        return "Not specified"
    return f"{currency_symbol}{budget:,.0f}"


def _build_new_lead_email(
    to_email: str,
    creator_name: str,
    brand_name: str,
    budget: Optional[float],
    currency_symbol: str,
) -> MIMEMultipart:
    dashboard_url = f"{settings.frontend_url.rstrip('/')}/leads"
    budget_line = _fmt_budget(budget, currency_symbol)
    from_addr = settings.smtp_from or settings.smtp_user

    # ── Plain text ────────────────────────────────────────
    text_body = (
        f"Hi {creator_name},\n\n"
        f"{brand_name} just submitted a pitch on PitchFlow.\n\n"
        f"Budget: {budget_line}\n\n"
        f"Review it here: {dashboard_url}\n\n"
        "— The PitchFlow team\n"
    )

    # ── HTML ──────────────────────────────────────────────
    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:40px 0;background:#faf9f7;font-family:Inter,system-ui,sans-serif;">
  <div style="max-width:480px;margin:0 auto;background:#ffffff;border-radius:12px;border:1px solid #e8e4de;padding:36px 32px;">

    <p style="margin:0 0 24px;font-size:12px;font-weight:600;letter-spacing:0.07em;
              text-transform:uppercase;color:#a0907f;">PitchFlow</p>

    <h1 style="margin:0 0 6px;font-size:20px;font-weight:600;color:#2e231e;letter-spacing:-0.01em;">
      New pitch received 🎉
    </h1>
    <p style="margin:0 0 28px;font-size:14px;color:#6b5e56;line-height:1.5;">
      Hi <strong>{creator_name}</strong>, <strong>{brand_name}</strong> just submitted a pitch on your form.
    </p>

    <!-- Detail card -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f2ef;border-radius:10px;padding:0;margin-bottom:28px;">
      <tr>
        <td style="padding:14px 18px 6px;">
          <span style="display:block;font-size:11px;color:#a0907f;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:3px;">Brand</span>
          <span style="font-size:14px;font-weight:500;color:#2e231e;">{brand_name}</span>
        </td>
      </tr>
      <tr>
        <td style="padding:6px 18px 14px;border-top:1px solid #e8e4de;">
          <span style="display:block;font-size:11px;color:#a0907f;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:3px;">Budget</span>
          <span style="font-size:14px;font-weight:500;color:#2e231e;font-variant-numeric:tabular-nums;">{budget_line}</span>
        </td>
      </tr>
    </table>

    <!-- CTA -->
    <a href="{dashboard_url}"
       style="display:block;text-align:center;background:#2e231e;color:#ffffff;
              font-size:13px;font-weight:500;text-decoration:none;
              border-radius:8px;padding:12px 20px;letter-spacing:-0.005em;">
      Review pitch →
    </a>

    <p style="margin:28px 0 0;font-size:12px;color:#c0b3aa;text-align:center;line-height:1.5;">
      You're receiving this because you're a PitchFlow creator.<br>
      <a href="{settings.frontend_url}" style="color:#c0b3aa;">pitchflow.in</a>
    </p>
  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"New pitch from {brand_name} — PitchFlow"
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["X-Mailer"] = "PitchFlow"
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


# ── SMTP transport ────────────────────────────────────────────────────────────

def _send_blocking(to_email: str, msg: MIMEMultipart) -> None:
    """Synchronous SMTP send. Runs inside a daemon thread."""
    from_addr = settings.smtp_from or settings.smtp_user
    try:
        if settings.smtp_use_tls and settings.smtp_port == 465:
            # Implicit TLS (SMTPS)
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(from_addr, [to_email], msg.as_string())
        else:
            # Explicit TLS via STARTTLS (default: port 587)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.ehlo()
                if settings.smtp_use_tls:
                    server.starttls()
                    server.ehlo()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(from_addr, [to_email], msg.as_string())

        logger.info("email.sent to=%s subject=%r", to_email, msg["Subject"])

    except smtplib.SMTPAuthenticationError:
        logger.error("email.auth_failed smtp_user=%s", settings.smtp_user)
    except smtplib.SMTPException as exc:
        logger.error("email.smtp_error to=%s error=%s", to_email, exc)
    except OSError as exc:
        logger.error("email.connection_error host=%s port=%s error=%s",
                     settings.smtp_host, settings.smtp_port, exc)


# ── Public API ────────────────────────────────────────────────────────────────

def send_new_lead_notification(
    *,
    to_email: str,
    creator_name: str,
    brand_name: str,
    budget: Optional[float] = None,
    currency_symbol: str = "$",
) -> None:
    """
    Fire-and-forget email notification to creator when a lead is submitted.

    No-ops silently when SMTP is not configured so dev environments are
    unaffected without .env SMTP vars.
    """
    if not settings.smtp_configured:
        logger.debug("email.skipped reason=smtp_not_configured")
        return

    msg = _build_new_lead_email(to_email, creator_name, brand_name, budget, currency_symbol)

    thread = threading.Thread(
        target=_send_blocking,
        args=(to_email, msg),
        daemon=True,
        name=f"pitchflow-email-{to_email}",
    )
    thread.start()
