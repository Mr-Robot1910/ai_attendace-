# ─────────────────────────────────────────────────────────────────────────────
# Gmail SMTP Configuration
# ─────────────────────────────────────────────────────────────────────────────
# 1. Open your Gmail → Settings → Security → Enable 2-Step Verification
# 2. Go to https://myaccount.google.com/apppasswords
# 3. Create an App Password for "Mail" → copy the 16-character password
# 4. Paste it below (remove the spaces)
# ─────────────────────────────────────────────────────────────────────────────

GMAIL_SENDER   = "rishikeshsinghrajput6@gmail.com"     # <-- replace with your Gmail address
GMAIL_APP_PASS = "lmsvwxwimexigged"       # <-- replace with your 16-char App Password

# ─────────────────────────────────────────────────────────────────────────────
# Admin PIN — used to protect the dashboard
# Change this to any numeric or alphanumeric PIN you want
# ─────────────────────────────────────────────────────────────────────────────
ADMIN_PIN    = '1234'          # <-- change to your preferred PIN
SECRET_KEY   = 'smartattend-secret-key-2026'  # <-- change to a long random string
