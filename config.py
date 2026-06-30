import os
import re
import logging
from logging.handlers import RotatingFileHandler
from os import environ

id_pattern = re.compile(r"^-?\d+$")

# ==========================
# Telegram
# ==========================
TG_BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
APP_ID = int(os.environ["APP_ID"])
API_HASH = os.environ["API_HASH"]

# ==========================
# Owner
# ==========================
OWNER_ID = int(os.environ["OWNER_ID"])
PORT = int(os.environ.get("PORT", "8080"))

# ==========================
# Database
# ==========================
DB_URI = os.environ["DB_URI"]
DB_NAME = os.environ.get("DB_NAME", "link")
DATABASE_CHANNEL = int(os.environ.get("DATABASE_CHANNEL", "0"))

# ==========================
# Workers
# ==========================
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "40"))

# ==========================
# Auto Approve
# ==========================
CHAT_ID = [
    int(x) if id_pattern.search(x) else x
    for x in environ.get("CHAT_ID", "").split()
]

TEXT = environ.get(
    "APPROVED_WELCOME_TEXT",
    "<b>{mention},\n\nYour request to join <b>{title}</b> has been approved.</b>"
)

APPROVED = environ.get("APPROVED_WELCOME", "on").lower()

# ==========================
# Images
# ==========================
START_PIC = "https://telegra.ph/file/f3d3aff9ec422158feb05-d2180e3665e0ac4d32.jpg"
START_IMG = START_PIC

# ==========================
# Messages
# ==========================
START_MSG = environ.get(
    "START_MESSAGE",
    """
👋 Welcome, {first}!

Thanks for using <b>Amon Links Share Bot</b>.

⚡ Your gateway to fast and secure temporary invite links.

━━━━━━━━━━━━━━━━━━

👑 <b>Owner:</b> Matrix (@xzrie)
📢 <b>Official Channel:</b> @MovieCrescent

💙 Thanks for being here. Enjoy your experience!
"""
)
HELP_MSG = environ.get(
    "HELP_MSG",
    """
🤖 <b>Amon Links Share Bot — Help</b>

Your gateway to fast and secure temporary invite links.

━━━━━━━━━━━━━━━━━━
📜 <b>Commands:</b>

/start — Start the bot and see the welcome message
/help — Show this help message

━━━━━━━━━━━━━━━━━━
📌 <b>How to Use:</b>

1️⃣ Start a chat with the bot using /start
2️⃣ Request an invite link as guided by the bot
3️⃣ Use the generated link to join the channel

⏳ <b>Note:</b> Invite links are temporary and will expire after a set period, so use them promptly.

━━━━━━━━━━━━━━━━━━
📢 <b>Official Channel:</b> @MovieCrescent

💙 Thank you for using Amon Links Share Bot!
"""
)
HELP = environ.get(
    "HELP_MESSAGE",
    "<b>Use /help to get help.</b>"
)

ABOUT = environ.get(
    "ABOUT_MESSAGE",
    "<b>Links Share Bot</b>"
)

ABOUT_TXT = """
<b>
Links Share Bot
<blockquote expandable>
Owner: @xzrie
Library: Pyrogram
Language: Python
Database: MongoDB
</blockquote>
</b>
"""

CHANNELS_TXT = """
<b>
Movie Crescent
<blockquote expandable>
https://t.me/MovieCrescent
</blockquote>
</b>
"""

# ==========================
# Stats
# ==========================
BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"

USER_REPLY_TEXT = "⚠️ You are not authorised to use this command."

# ==========================
# Admins
# ==========================
try:
    ADMINS = [
        int(x)
        for x in environ.get("ADMINS", str(OWNER_ID)).split()
        if x
    ]
except ValueError:
    raise Exception("ADMINS must contain only integer IDs.")

if OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)

# ==========================
# Logging
# ==========================
LOG_FILE_NAME = "links-sharingbot.txt"

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

def LOGGER(name):
    return logging.getLogger(name)