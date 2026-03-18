"""
Email notification service using Gmail SMTP.
Configure your Gmail credentials in config.py:
    GMAIL_SENDER  = "your.email@gmail.com"
    GMAIL_APP_PASS = "xxxx xxxx xxxx xxxx"  # 16-char Gmail App Password
"""
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ─── Load config safely ──────────────────────────────────────────────────────
try:
    from config import GMAIL_SENDER, GMAIL_APP_PASS
except ImportError:
    GMAIL_SENDER   = ""
    GMAIL_APP_PASS = ""


def _is_configured() -> bool:
    return bool(GMAIL_SENDER and GMAIL_APP_PASS)


def _send(to_email: str, subject: str, body_html: str) -> bool:
    """Core sending logic. Returns True on success."""
    if not _is_configured():
        print("[Email] Not configured — skipping email.")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"AI Attendance System <{GMAIL_SENDER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASS)
            server.sendmail(GMAIL_SENDER, to_email, msg.as_string())
        print(f"[Email] ✅ Sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[Email] ❌ Failed to send to {to_email}: {e}")
        return False


def send_async(to_email: str, subject: str, body_html: str):
    """Fire-and-forget: send email in a background thread so the feed isn't blocked."""
    threading.Thread(target=_send, args=(to_email, subject, body_html), daemon=True).start()


# ─── Email templates ─────────────────────────────────────────────────────────

def _base_template(content: str) -> str:
    return f"""
    <html><body style="margin:0;padding:0;background:#0f172a;font-family:'Segoe UI',sans-serif;">
      <div style="max-width:520px;margin:30px auto;background:#1e293b;border-radius:16px;
                  overflow:hidden;border:1px solid rgba(99,102,241,0.3);box-shadow:0 20px 60px rgba(0,0,0,0.5);">
        <div style="background:linear-gradient(135deg,#6366f1,#ec4899);padding:28px 32px;">
          <div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.5px;">
            🎓 AI Attendance System
          </div>
          <div style="color:rgba(255,255,255,0.75);font-size:13px;margin-top:4px;">
            Automated Attendance Notification
          </div>
        </div>
        <div style="padding:28px 32px;color:#cbd5e1;">
          {content}
        </div>
        <div style="padding:16px 32px;background:rgba(0,0,0,0.2);
                    font-size:12px;color:#64748b;text-align:center;">
          This is an automated message from your college AI Attendance System.
        </div>
      </div>
    </body></html>
    """


def send_present_email(to_email: str, name: str, roll_no: str):
    """Send a 'marked present' notification."""
    date_str = datetime.now().strftime("%d %B %Y")
    time_str = datetime.now().strftime("%I:%M %p")

    content = f"""
      <h2 style="color:#10b981;margin:0 0 16px;">✅ Attendance Marked — Present</h2>
      <p>Hi <strong style="color:#fff">{name}</strong>,</p>
      <p>Your attendance has been successfully recorded for today.</p>
      <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);
                  border-radius:10px;padding:16px 20px;margin:20px 0;">
        <table style="width:100%;border-collapse:collapse;color:#94a3b8;font-size:14px;">
          <tr><td style="padding:5px 0;">👤 Name</td>
              <td style="color:#fff;font-weight:600;text-align:right">{name}</td></tr>
          <tr><td style="padding:5px 0;">🎫 Roll No</td>
              <td style="color:#fff;font-weight:600;text-align:right">{roll_no}</td></tr>
          <tr><td style="padding:5px 0;">📅 Date</td>
              <td style="color:#fff;font-weight:600;text-align:right">{date_str}</td></tr>
          <tr><td style="padding:5px 0;">⏰ Time</td>
              <td style="color:#fff;font-weight:600;text-align:right">{time_str}</td></tr>
          <tr><td style="padding:5px 0;">📊 Status</td>
              <td style="color:#10b981;font-weight:700;text-align:right">✅ Present</td></tr>
        </table>
      </div>
      <p style="font-size:13px;color:#64748b;">No action required. Have a great day!</p>
    """
    send_async(to_email, f"✅ Attendance Confirmed — {date_str}", _base_template(content))


def send_absent_email(to_email: str, name: str, roll_no: str):
    """Send an 'absent' notification at the end of a session."""
    date_str = datetime.now().strftime("%d %B %Y")

    content = f"""
      <h2 style="color:#ef4444;margin:0 0 16px;">⚠️ Attendance Not Recorded — Absent</h2>
      <p>Hi <strong style="color:#fff">{name}</strong>,</p>
      <p>Your attendance was <strong style="color:#ef4444">not recorded</strong> during today's session.
         You have been marked <strong>Absent</strong>.</p>
      <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
                  border-radius:10px;padding:16px 20px;margin:20px 0;">
        <table style="width:100%;border-collapse:collapse;color:#94a3b8;font-size:14px;">
          <tr><td style="padding:5px 0;">👤 Name</td>
              <td style="color:#fff;font-weight:600;text-align:right">{name}</td></tr>
          <tr><td style="padding:5px 0;">🎫 Roll No</td>
              <td style="color:#fff;font-weight:600;text-align:right">{roll_no}</td></tr>
          <tr><td style="padding:5px 0;">📅 Date</td>
              <td style="color:#fff;font-weight:600;text-align:right">{date_str}</td></tr>
          <tr><td style="padding:5px 0;">📊 Status</td>
              <td style="color:#ef4444;font-weight:700;text-align:right">❌ Absent</td></tr>
        </table>
      </div>
      <p style="font-size:13px;color:#64748b;">
        If you believe this is an error, please contact your instructor.
      </p>
    """
    send_async(to_email, f"⚠️ You Were Marked Absent — {date_str}", _base_template(content))
