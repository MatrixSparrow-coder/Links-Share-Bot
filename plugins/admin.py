# +++ Movie Crescent — Admin Module
# Bot: Amon (@LinkShare1_bot)
# Owner: @xzrie
# Channel: @MovieCrescent

from config import *
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, ChatAdminRequired
from database.database import set_approval_off, is_approval_off, add_admin, remove_admin, list_admins

_HEADER = "<b>🎬 Movie Crescent — Links Share Bot</b>"
_FOOTER = "\n<i>— Amon | @MovieCrescent</i>"


@Client.on_message(filters.command("addadmin") & filters.user(OWNER_ID))
async def add_admin_command(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            f"{_HEADER}\n\n"
            "Usage: <code>/addadmin {user_id}</code>"
            f"{_FOOTER}"
        )

    raw = message.command[1]
    if not raw.isdigit() or int(raw) <= 0:
        return await message.reply_text(
            f"{_HEADER}\n\n"
            "❌ Invalid user ID"
            f"{_FOOTER}"
        )

    user_id = int(raw)
    try:
        success = await add_admin(user_id)
    except Exception:
        return await message.reply_text(
            f"{_HEADER}\n\n"
            "⚠️ Database error occurred. Try again later."
            f"{_FOOTER}"
        )

    if success:
        await message.reply_text(
            f"{_HEADER}\n\n"
            f"✅ User <code>{user_id}</code> added as admin."
            f"{_FOOTER}"
        )
    else:
        await message.reply_text(
            f"{_HEADER}\n\n"
            f"❌ Failed to add admin <code>{user_id}</code>."
            f"{_FOOTER}"
        )


@Client.on_message(filters.command("deladmin") & filters.user(OWNER_ID))
async def del_admin_command(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            f"{_HEADER}\n\n"
            "Usage: <code>/deladmin {user_id}</code>"
            f"{_FOOTER}"
        )

    raw = message.command[1]
    if not raw.isdigit() or int(raw) <= 0:
        return await message.reply_text(
            f"{_HEADER}\n\n"
            "❌ Invalid user ID"
            f"{_FOOTER}"
        )

    user_id = int(raw)
    try:
        success = await remove_admin(user_id)
    except Exception:
        return await message.reply_text(
            f"{_HEADER}\n\n"
            "⚠️ Database error occurred. Try again later."
            f"{_FOOTER}"
        )

    if success:
        await message.reply_text(
            f"{_HEADER}\n\n"
            f"✅ User <code>{user_id}</code> removed from admins."
            f"{_FOOTER}"
        )
    else:
        await message.reply_text(
            f"{_HEADER}\n\n"
            f"❌ Failed to remove admin <code>{user_id}</code>."
            f"{_FOOTER}"
        )


@Client.on_message(filters.command("admins") & filters.user(OWNER_ID))
async def list_admins_command(client, message: Message):
    try:
        admins = await list_admins()
    except Exception:
        return await message.reply_text(
            f"{_HEADER}\n\n"
            "⚠️ Database error occurred. Try again later."
            f"{_FOOTER}"
        )

    if not admins:
        return await message.reply_text(
            f"{_HEADER}\n\n"
            "No admins found."
            f"{_FOOTER}"
        )

    uid_list = "\n".join([f"<code>{uid}</code>" for uid in admins])
    await message.reply_text(
        f"{_HEADER}\n\n"
        f"<b>Admin User IDs:</b>\n{uid_list}"
        f"{_FOOTER}"
)
