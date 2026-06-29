        # +++ Movie Crescent — Auto Approval Module
# Bot: Amon (@LinkShare1_bot)
# Owner: @xzrie
# Channel: @MovieCrescent

import asyncio
import logging
from config import *
from pyrogram import Client, filters
from pyrogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, RPCError, UserNotParticipant
from database.database import set_approval_off, is_approval_off
from helper_func import *

logger = logging.getLogger(__name__)

# Default settings
APPROVAL_WAIT_TIME = 5       # seconds
AUTO_APPROVE_ENABLED = True  # Toggle for enabling/disabling auto approval

# Safe userbot initialization
user_client = None

async def get_user_client():
    global user_client
    if user_client is None:
        try:
            user_client = UserClient(
                "userbot",
                session_string=USER_SESSION,
                api_id=APP_ID,
                api_hash=API_HASH
            )
            await user_client.start()
            logger.info("Userbot client started successfully.")
        except Exception as e:
            logger.error(f"Failed to start userbot client: {e}")
            user_client = None
    return user_client


@Client.on_chat_join_request(
    (filters.group | filters.channel) & filters.chat(CHAT_ID)
    if CHAT_ID else (filters.group | filters.channel)
)
async def autoapprove(client, message: ChatJoinRequest):
    global AUTO_APPROVE_ENABLED

    if not AUTO_APPROVE_ENABLED:
        return

    chat = message.chat
    user = message.from_user

    # Check if approval is disabled for this channel
    if await is_approval_off(chat.id):
        logger.info(f"Auto-approval is OFF for channel {chat.id}")
        return

    logger.info(f"{user.first_name} requested to join {chat.title}")

    await asyncio.sleep(APPROVAL_WAIT_TIME)

    # Skip if user is already a participant
    try:
        member = await client.get_chat_member(chat.id, user.id)
        if member.status in ["member", "administrator", "creator"]:
            logger.info(f"User {user.id} is already in {chat.id}, skipping approval.")
            return
    except UserNotParticipant:
        pass  # Not a member — proceed with approval
    except Exception as e:
        logger.warning(f"Could not check membership for {user.id} in {chat.id}: {e}")

    # Approve the join request safely
    try:
        await client.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
        logger.info(f"Approved {user.id} for {chat.id}")
    except FloodWait as e:
        logger.warning(f"FloodWait: sleeping {e.value}s before retrying approval.")
        await asyncio.sleep(e.value)
        try:
            await client.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
        except Exception as retry_err:
            logger.error(f"Retry approval failed for {user.id}: {retry_err}")
            return
    except RPCError as e:
        logger.error(f"RPCError approving {user.id} in {chat.id}: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error approving {user.id}: {e}")
        return

    # Send approval notification if APPROVED is defined and set to "on"
    if globals().get("APPROVED", "").lower() == "on":
        try:
            invite_link = await client.export_chat_invite_link(chat.id)
            buttons = [
                [InlineKeyboardButton("• ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇs •", url="https://t.me/MovieCrescent")],
                [InlineKeyboardButton(f"• ᴊᴏɪɴ {chat.title} •", url=invite_link)]
            ]
            markup = InlineKeyboardMarkup(buttons)
            caption = (
                f"<b>ʜᴇʏ {user.mention()},\n\n"
                f"<blockquote>ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {chat.title} "
                f"ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ.</blockquote></b>"
            )
            await client.send_photo(
                chat_id=user.id,
                photo="https://telegra.ph/file/f3d3aff9ec422158feb05-d2180e3665e0ac4d32.jpg",
                caption=caption,
                reply_markup=markup
            )
        except Exception as e:
            logger.warning(f"Could not send approval DM to {user.id}: {e}")


@Client.on_message(filters.command("reqtime") & is_owner_or_admin)
async def set_reqtime(client, message: Message):
    global APPROVAL_WAIT_TIME

    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("Usage: <code>/reqtime {seconds}</code>")

    APPROVAL_WAIT_TIME = int(message.command[1])
    await message.reply_text(
        f"✅ Request approval wait time set to <b>{APPROVAL_WAIT_TIME}</b> seconds."
    )


@Client.on_message(filters.command("reqmode") & is_owner_or_admin)
async def toggle_reqmode(client, message: Message):
    global AUTO_APPROVE_ENABLED

    if len(message.command) != 2 or message.command[1].lower() not in ["on", "off"]:
        return await message.reply_text(
            "Usage: <code>/reqmode on</code> or <code>/reqmode off</code>"
        )

    mode = message.command[1].lower()
    AUTO_APPROVE_ENABLED = (mode == "on")
    status = "enabled ✅" if AUTO_APPROVE_ENABLED else "disabled ❌"
    await message.reply_text(f"Auto-approval has been <b>{status}</b>.")


@Client.on_message(filters.command("approveoff") & is_owner_or_admin)
async def approve_off_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply_text("Usage: <code>/approveoff {channel_id}</code>")

    channel_id = int(message.command[1])
    try:
        success = await set_approval_off(channel_id, True)
    except Exception as e:
        logger.error(f"DB error in approveoff: {e}")
        return await message.reply_text("⚠️ Database error occurred. Try again later.")

    if success:
        await message.reply_text(
            f"✅ Auto-approval is now <b>OFF</b> for channel <code>{channel_id}</code>."
        )
    else:
        await message.reply_text(
            f"❌ Failed to disable auto-approval for channel <code>{channel_id}</code>."
        )


@Client.on_message(filters.command("approveon") & is_owner_or_admin)
async def approve_on_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply_text("Usage: <code>/approveon {channel_id}</code>")

    channel_id = int(message.command[1])
    try:
        success = await set_approval_off(channel_id, False)
    except Exception as e:
        logger.error(f"DB error in approveon: {e}")
        return await message.reply_text("⚠️ Database error occurred. Try again later.")

    if success:
        await message.reply_text(
            f"✅ Auto-approval is now <b>ON</b> for channel <code>{channel_id}</code>."
        )
    else:
        await message.reply_text(
            f"❌ Failed to enable auto-approval for channel <code>{channel_id}</code>."
            )
                
