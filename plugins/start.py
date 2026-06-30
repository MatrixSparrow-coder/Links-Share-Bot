# ============================================================
# Links Share Bot — Amon
# Owner  : Matrix (@xzrie)
# Channel: @MovieCrescent
# ============================================================

import asyncio
import time
from asyncio import Lock
from collections import defaultdict
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot import Bot
from config import *
from database.database import *
from helper_func import *
from plugins.newpost import revoke_invite_after_5_minutes

# ── Per-channel lock to prevent concurrent invite-link generation ──────────────
channel_locks: defaultdict = defaultdict(asyncio.Lock)

# ── Spam-ban state ─────────────────────────────────────────────────────────────
user_banned_until: dict = {}

# ── Broadcast cancel state ─────────────────────────────────────────────────────
cancel_lock: Lock = asyncio.Lock()
is_canceled: bool = False

# ── Anti-spam constants ────────────────────────────────────────────────────────
user_message_count: dict = {}
MAX_MESSAGES: int = 3
TIME_WINDOW: timedelta = timedelta(seconds=10)
BAN_DURATION: timedelta = timedelta(hours=1)

# ── Cached chat metadata ───────────────────────────────────────────────────────
chat_data_cache: dict = {}

# ── Misc message templates ─────────────────────────────────────────────────────
WAIT_MSG = "<b>Please wait…</b>"
REPLY_ERROR = "Use this command as a reply to any Telegram message without extra spaces."

# ── Static display info (UI only — no backend impact) ─────────────────────────
BOT_NAME = "Amon Links Share Bot"
BOT_OWNER = "Matrix (@xzrie)"
BOT_CHANNEL = "@MovieCrescent"
BOT_VERSION = "2.0"


def main_menu_buttons() -> InlineKeyboardMarkup:
    """Primary inline keyboard shown on the /start welcome screen."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
                InlineKeyboardButton("📢 Channels", callback_data="channels"),
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
                InlineKeyboardButton("✖️ Close", callback_data="close"),
            ],
        ]
    )


def back_button() -> InlineKeyboardMarkup:
    """Single back button used on all sub-pages."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
    )


# ==============================================================================
#  /start  handler
# ==============================================================================

@Bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Bot, message: Message):
    user_id = message.from_user.id

    # ── Spam-ban check ─────────────────────────────────────────────────────────
    if user_id in user_banned_until:
        if datetime.now() < user_banned_until[user_id]:
            return await message.reply_text(
                "<b><blockquote expandable>"
                "⚠️ You have been temporarily restricted due to excessive requests.\n"
                "Please wait a while before trying again."
                "</blockquote></b>",
                parse_mode=ParseMode.HTML,
            )

    await add_user(user_id)

    # ── Force-Subscribe checks (disabled — uncomment to enable) ───────────────
    # if not await is_subscribed(client, user_id):
    #     return await not_joined(client, message)

    # fsub_channels = await get_fsub_channels()
    # if fsub_channels:
    #     is_subbed, sub_msg, sub_btns = await check_subscription_status(
    #         client, user_id, fsub_channels
    #     )
    #     if not is_subbed:
    #         return await message.reply_text(
    #             sub_msg, reply_markup=sub_btns, parse_mode=ParseMode.HTML
    #         )

    text = message.text

    # ── Deep-link payload present ──────────────────────────────────────────────
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            is_request = base64_string.startswith("req_")

            if is_request:
                base64_string = base64_string[4:]
                channel_id = await get_channel_by_encoded_link2(base64_string)
            else:
                channel_id = await get_channel_by_encoded_link(base64_string)

            if not channel_id:
                return await message.reply_text(
                    "<b><blockquote expandable>"
                    "❌ This link is invalid or has already expired.\n"
                    "Please request a fresh link from the original post."
                    "</blockquote></b>",
                    parse_mode=ParseMode.HTML,
                )

            # ── Check for a static /genlink URL ───────────────────────────────
            from database.database import get_original_link

            original_link = await get_original_link(channel_id)
            if original_link:
                button = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("• Proceed to Link •", url=original_link)]]
                )
                return await message.reply_text(
                    "<b><blockquote expandable>"
                    "✅ Your link is ready! Tap the button below to continue."
                    "</blockquote></b>",
                    reply_markup=button,
                    parse_mode=ParseMode.HTML,
                )

            # ── Invite-link generation (with per-channel lock) ─────────────────
            async with channel_locks[channel_id]:
                old_link_info = await get_current_invite_link(channel_id)
                current_time = datetime.now()

                if old_link_info:
                    link_created_time = await get_link_creation_time(channel_id)
                    # Reuse the link if it was created less than 4 minutes ago
                    if link_created_time and (
                        current_time - link_created_time
                    ).total_seconds() < 240:
                        invite_link = old_link_info["invite_link"]
                        is_request_link = old_link_info["is_request"]
                    else:
                        # Revoke stale link and issue a new one
                        try:
                            await client.revoke_chat_invite_link(
                                channel_id, old_link_info["invite_link"]
                            )
                            print(
                                f"[Amon] Revoked stale "
                                f"{'request' if old_link_info['is_request'] else 'invite'} "
                                f"link for channel {channel_id}"
                            )
                        except Exception as e:
                            print(
                                f"[Amon] Could not revoke old link for {channel_id}: {e}"
                            )

                        invite = await client.create_chat_invite_link(
                            chat_id=channel_id,
                            expire_date=current_time + timedelta(minutes=10),
                            creates_join_request=is_request,
                        )
                        invite_link = invite.invite_link
                        is_request_link = is_request
                        await save_invite_link(channel_id, invite_link, is_request_link)
                else:
                    # No prior link — create one fresh
                    invite = await client.create_chat_invite_link(
                        chat_id=channel_id,
                        expire_date=current_time + timedelta(minutes=10),
                        creates_join_request=is_request,
                    )
                    invite_link = invite.invite_link
                    is_request_link = is_request
                    await save_invite_link(channel_id, invite_link, is_request_link)

            button_text = (
                "• ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ •" if is_request_link else "• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •"
            )
            button = InlineKeyboardMarkup(
                [[InlineKeyboardButton(button_text, url=invite_link)]]
            )

            # Brief loading indicator then delete
            wait_msg = await message.reply_text("⏳", parse_mode=ParseMode.HTML)
            await wait_msg.delete()

            await message.reply_text(
                "<b><blockquote expandable>"
                "✅ Your link is ready! Tap the button below to continue."
                "</blockquote></b>",
                reply_markup=button,
                parse_mode=ParseMode.HTML,
            )

            note_msg = await message.reply_text(
                "<b><u>📌 Note:</u></b> Links expire after a short time. "
                "If yours has expired, simply tap the original post link to get a new one.",
                parse_mode=ParseMode.HTML,
            )

            # Auto-delete the note after 5 minutes
            asyncio.create_task(delete_after_delay(note_msg, 300))

            # Schedule invite-link revocation after 5 minutes
            asyncio.create_task(
                revoke_invite_after_5_minutes(
                    client, channel_id, invite_link, is_request_link
                )
            )

        except Exception as e:
            await message.reply_text(
                "<b><blockquote expandable>"
                "❌ This link is invalid or has already expired.\n"
                "Please request a fresh link from the original post."
                "</blockquote></b>",
                parse_mode=ParseMode.HTML,
            )
            print(f"[Amon] Deep-link decode error: {e}")

    # ── No deep-link payload — show welcome screen ─────────────────────────────
    else:
        inline_buttons = main_menu_buttons()

        wait_msg = await message.reply_text("⏳")
        await asyncio.sleep(0.1)
        await wait_msg.delete()

        try:
            await message.reply_photo(
                photo=START_PIC,
                caption=START_MSG,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[Amon] Could not send start photo: {e}")
            await message.reply_text(
                START_MSG,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML,
            )


# ==============================================================================
#  Utility — invite-link creation timestamp
# ==============================================================================

async def get_link_creation_time(channel_id):
    """Return the creation timestamp of the active invite link for *channel_id*."""
    try:
        from database.database import channels_collection

        channel = await channels_collection.find_one(
            {"channel_id": channel_id, "status": "active"}
        )
        if channel and "invite_link_created_at" in channel:
            return channel["invite_link_created_at"]
        return None
    except Exception as e:
        print(f"[Amon] Error fetching link creation time for {channel_id}: {e}")
        return None


# ==============================================================================
#  Force-Subscribe — not-joined handler
# ==============================================================================

async def not_joined(client: Client, message: Message):
    user_id = message.from_user.id
    buttons = []

    try:
        all_channels = await db.show_channels()

        for _, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)
            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_sub(client, user_id, chat_id):
                try:
                    # Use cached chat metadata where possible
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title

                    if mode == "on" and not data.username:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=(
                                datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY)
                                if FSUB_LINK_EXPIRY
                                else None
                            ),
                        )
                        link = invite.invite_link
                    else:
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=(
                                    datetime.utcnow()
                                    + timedelta(seconds=FSUB_LINK_EXPIRY)
                                    if FSUB_LINK_EXPIRY
                                    else None
                                ),
                            )
                            link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])

                except Exception as e:
                    print(f"[Amon] Error building FSub button for {chat_id}: {e}")
                    return

        # Retry button
        try:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="♻️ Try Again",
                        url=f"https://t.me/{client.username}?start={message.command[1]}",
                    )
                ]
            )
        except IndexError:
            pass

        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=(
                    None
                    if not message.from_user.username
                    else "@" + message.from_user.username
                ),
                mention=message.from_user.mention,
                id=message.from_user.id,
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        print(f"[Amon] not_joined error: {e}")


# ==============================================================================
#  Callback queries
# ==============================================================================

@Bot.on_callback_query(filters.regex("close"))
async def close_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except Exception as e:
        print(f"[Amon] close_callback delete error: {e}")