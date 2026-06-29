import os
import re
import logging
from logging.handlers import RotatingFileHandler

id_pattern = re.compile(r'^-?\d+$')

# ─────────────────────────────
# Telegram API (IMPORTANT FIX)
# ─────────────────────────────
APP_ID = int(os.environ["APP_ID"])
API_HASH = os.environ["API_HASH"]
TG_BOT_TOKEN = os.environ["TG_BOT_TOKEN"]

# ─────────────────────────────
# Owner & Access
# ─────────────────────────────
OWNER_ID = int(os.environ.get("OWNER_ID", "8662719308"))
PORT = int(os.environ.get("PORT", "8080"))

# ─────────────────────────────
# Database
# ─────────────────────────────
DB_URI = os.environ.get("DB_URI", "")
DB_NAME = os.environ.get("DB_NAME", "link")

# ─────────────────────────────
# Worker Threads
# ─────────────────────────────
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "40"))

# ─────────────────────────────
# Admins
# ─────────────────────────────
try:
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "").split() if x]
except ValueError:
    raise Exception("ADMINS must contain valid integer IDs")

if OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)

# ─────────────────────────────
# Logger
# ─────────────────────────────
LOG_FILE_NAME = "links-bot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE_NAME, maxBytes=50000000, backupCount=10),
        logging.StreamHandler()
    ]
)

def LOGGER(name: str):
    return logging.getLogger(name)