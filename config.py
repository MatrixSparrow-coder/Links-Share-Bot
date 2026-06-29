import os
from os import environ
import logging
from logging.handlers import RotatingFileHandler

import re
id_pattern = re.compile(r'^-?\d+$')

# ─────────────────────────────────────────────
# Telegram API Credentials
# ─────────────────────────────────────────────
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID       = int(os.environ.get("APP_ID", "0"))
API_HASH     = os.environ.get("API_HASH", "")

# ─────────────────────────────────────────────
# Owner & Access
# ─────────────────────────────────────────────
OWNER_ID = int(os.environ.get("OWNER_ID", "8662719308"))
PORT     = os.environ.get("PORT", "8080")

# ─────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────
DB_URI  = os.environ.get("DB_URI", "")
DB_NAME = os.environ.get("DB_NAME", "link")

# ─────────────────────────────────────────────
# Auto Approve
# ─────────────────────────────────────────────
CHAT_ID  = [
    int(app_chat_id) if id_pattern.search(app_chat_id) else app_chat_id
    for app_chat_id in environ.get("CHAT_ID", "").split()
]
TEXT     = environ.get(
    "APPROVED_WELCOME_TEXT",
    "<b>{mention},\n\nYour request to join <b>{title}</b> has been approved.\n\n"
    "Powered by @MovieCrescent</b>"
)
APPROVED = environ.get("APPROVED_WELCOME", "on").lower()

# ─────────────────────────────────────────────
# Worker Threads
# ─────────────────────────────────────────────
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "40"))

# ─────────────────────────────────────────────
# Media
# ─────────────────────────────────────────────
START_PIC = "https://telegra.ph/file/f3d3aff9ec422158feb05-d2180e3665e0ac4d32.jpg"
START_IMG = "https://telegra.ph/file/f3d3aff9ec422158feb05-d2180e3665e0ac4d32.jpg"

# ─────────────────────────────────────────────
# Bot Messages
# ─────────────────────────────────────────────
START_MSG = os.environ.get(
    "START_MESSAGE",
    "<b>Welcome to Links Share Bot — Amon ⚡\n\n"
    "Share channel links securely and protect your channels from copyright issues.\n\n"
    "Powered by @MovieCrescent</b>"
)

HELP = os.environ.get(
    "HELP_MESSAGE",
    "<b>Need help? Here's how to get started:\n\n"
    "• Use /addch to add a channel\n"
    "• Use /reqlink to request a link\n"
    "• Use /stats to view bot statistics\n\n"
    "For support, visit @MovieCrescent</b>"
)

ABOUT = os.environ.get(
    "ABOUT_MESSAGE",
    "<b>Links Share Bot (Amon) generates secure, temporary invite links "
    "for private Telegram channels — keeping your content safe and access controlled.\n\n"
    "Powered by @MovieCrescent</b>"
)

ABOUT_TXT = (
    "<b>Links Share Bot\n"
    "<blockquote expandable>"
    "› Owner: <a href='https://t.me/xzrie'>Matrix</a>\n"
    "› Channel: <a href='https://t.me/MovieCrescent'>@MovieCrescent</a>\n"
    "› Language: <a href='https://docs.python.org/3/'>Python 3</a>\n"
    "› Library: <a href='https://docs.pyrogram.org/'>Pyrogram v2</a>\n"
    "› Database: <a href='https://www.mongodb.com/docs/'>MongoDB</a>\n"
    "</blockquote></b>"
)

CHANNELS_TXT = (
    "<b>Our Channels\n"
    "<blockquote expandable>"
    "› Main Channel: <a href='https://t.me/MovieCrescent'>@MovieCrescent</a>\n"
    "› Owner: <a href='https://t.me/xzrie'>@xzrie</a>"
    "</blockquote></b>"
)

# ─────────────────────────────────────────────
# Misc
# ─────────────────────────────────────────────
BOT_STATS_TEXT  = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "⚠️ You are not authorised to use this command."

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_FILE_NAME = "links-sharingbot.txt"

DATABASE_CHANNEL = int(os.environ.get("DATABASE_CHANNEL", "0"))

# ─────────────────────────────────────────────
# Admins
# ─────────────────────────────────────────────
try:
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "").split() if x]
except ValueError:
    raise Exception("ADMINS must contain valid integer Telegram user IDs only.")

if OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)

# ─────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
