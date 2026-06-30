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
                caption=START_MSG.format(
                    first=message.from_user.first_name,
                    mention=message.from_user.mention,
                ),
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[Amon] Could not send start photo: {e}")
            await message.reply_text(
                START_MSG.format(
                    first=message.from_user.first_name,
                    mention=message.from_user.mention,
                ),
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
@Bot.on_callback_query(filters.regex("^about$"))
async def about_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()

    about_text = (
        "<b>ℹ️ About This Bot</b>\n\n"
        "<blockquote>"
        f"🤖 <b>Name</b>      : {BOT_NAME}\n"
        f"👤 <b>Owner</b>     : {BOT_OWNER}\n"
        f"📢 <b>Channel</b>   : {BOT_CHANNEL}\n"
        f"🏷 <b>Version</b>   : {BOT_VERSION}\n"
        "🐍 <b>Language</b>  : Python\n"
        "📦 <b>Library</b>   : Pyrogram"
        "</blockquote>\n\n"
        "<i>Built to make sharing links fast, safe and simple.</i>"
    )

    try:
        await callback_query.message.edit_caption(
            caption=about_text,
            reply_markup=back_button(),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await callback_query.message.edit_text(
            about_text,
            reply_markup=back_button(),
            parse_mode=ParseMode.HTML,
        )


@Bot.on_callback_query(filters.regex("^channels$"))
async def channels_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()

    channels_text = (
        "<b>📢 Official Channel</b>\n\n"
        "<blockquote>Stay updated and grab the latest links from our official channel.</blockquote>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{BOT_CHANNEL.lstrip('@')}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")],
        ]
    )

    try:
        await callback_query.message.edit_caption(
            caption=channels_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await callback_query.message.edit_text(
            channels_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
        )


@Bot.on_callback_query(filters.regex("^help$"))
async def help_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()

    help_text = (
        "<b>❓ Help & Commands</b>\n\n"
        f"<i>{BOT_NAME} lets you fetch and share links shared in our channels.</i>\n\n"
        "<b>Basic Commands</b>\n"
        "<blockquote>"
        "/start — Launch the bot\n"
        "/help — Show this help page\n"
        "/info — Bot information"
        "</blockquote>\n\n"
        "<i>Need more help? Reach out to the owner.</i>"
    )

    try:
        await callback_query.message.edit_caption(
            caption=help_text,
            reply_markup=back_button(),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await callback_query.message.edit_text(
            help_text,
            reply_markup=back_button(),
            parse_mode=ParseMode.HTML,
        )


@Bot.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()

    try:
        await callback_query.message.edit_caption(
            caption=START_MSG,
            reply_markup=main_menu_buttons(),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await callback_query.message.edit_text(
            START_MSG,
            reply_markup=main_menu_buttons(),
            parse_mode=ParseMode.HTML,
        )


@Bot.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    fsub_channels = await get_fsub_channels()

    if not fsub_channels:
        return await callback_query.message.edit_text(
            "<b>No Force-Subscribe channels are configured at this time.</b>",
            parse_mode=ParseMode.HTML,
        )

    is_subbed, sub_msg, sub_btns = await check_subscription_status(
        client, user_id, fsub_channels
    )

    if is_subbed:
        await callback_query.message.edit_text(
            "<b>✅ You are subscribed to all required channels.\nSend /start to continue.</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await callback_query.message.edit_text(
            sub_msg,
            reply_markup=sub_btns,
            parse_mode=ParseMode.HTML,
        )


# ==============================================================================
#  Admin — /status
# ==============================================================================

@Bot.on_message(filters.command("status") & filters.private & is_owner_or_admin)
async def status_command(client: Bot, message: Message):
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("• Close •", callback_data="close")]]
    )

    start_time = time.time()
    temp_msg = await message.reply(
        "<b><i>Fetching stats…</i></b>", quote=True, parse_mode=ParseMode.HTML
    )
    ping_time = (time.time() - start_time) * 1000

    users = await full_userbase()
    delta = datetime.now() - client.uptime
    uptime_str = get_readable_time(delta.seconds)

    await temp_msg.edit(
        f"<b>"
        f"👤 Total Users : <code>{len(users)}</code>\n\n"
        f"⏱ Uptime       : <code>{uptime_str}</code>\n\n"
        f"📡 Ping         : <code>{ping_time:.2f} ms</code>"
        f"</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )


# ==============================================================================
#  Admin — /cancel  (stops an active broadcast)
# ==============================================================================

@Bot.on_message(filters.command("cancel") & filters.private & is_owner_or_admin)
async def cancel_broadcast(client: Bot, message: Message):
    global is_canceled
    async with cancel_lock:
        is_canceled = True
    await message.reply_text(
        "<b>🛑 Broadcast cancellation requested.</b>",
        parse_mode=ParseMode.HTML,
    )


# ==============================================================================
#  Admin — /broadcast
# ==============================================================================

@Bot.on_message(filters.private & filters.command("broadcast") & is_owner_or_admin)
async def broadcast(client: Bot, message: Message):
    global is_canceled
    args = message.text.split()[1:]

    if not message.reply_to_message:
        msg = await message.reply(
            "<b>Reply to a message to start a broadcast.</b>\n\n"
            "<b>Usage examples:</b>\n"
            "<code>/broadcast normal</code>\n"
            "<code>/broadcast pin</code>\n"
            "<code>/broadcast delete 30</code>\n"
            "<code>/broadcast pin delete 30</code>\n"
            "<code>/broadcast silent</code>",
            parse_mode=ParseMode.HTML,
        )
        await asyncio.sleep(8)
        return await msg.delete()

    # Parse broadcast mode flags
    do_pin = False
    do_delete = False
    duration = 0
    silent = False
    mode_text = []

    i = 0
    while i < len(args):
        arg = args[i].lower()
        if arg == "pin":
            do_pin = True
            mode_text.append("PIN")
        elif arg == "delete":
            do_delete = True
            try:
                duration = int(args[i + 1])
                i += 1
            except (IndexError, ValueError):
                return await message.reply(
                    "<b>Please provide a valid duration for delete mode.</b>\n"
                    "Usage: <code>/broadcast delete 30</code>",
                    parse_mode=ParseMode.HTML,
                )
            mode_text.append(f"DELETE({duration}s)")
        elif arg == "silent":
            silent = True
            mode_text.append("SILENT")
        else:
            mode_text.append(arg.upper())
        i += 1

    if not mode_text:
        mode_text.append("NORMAL")

    # Reset cancel flag before starting
    async with cancel_lock:
        is_canceled = False

    query = await full_userbase()
    broadcast_msg = message.reply_to_message
    total = len(query)
    successful = blocked = deleted = unsuccessful = 0

    mode_label = " + ".join(mode_text)
    pls_wait = await message.reply(
        f"<i>📤 Starting broadcast in <b>{mode_label}</b> mode…</i>",
        parse_mode=ParseMode.HTML,
    )

    bar_length = 20
    progress_bar = ""
    last_update_percentage = 0
    update_interval = 0.05  # update every 5 %

    for i, chat_id in enumerate(query, start=1):
        async with cancel_lock:
            if is_canceled:
                await pls_wait.edit(
                    f"<b>›› BROADCAST ({mode_label}) — CANCELED ❌</b>",
                    parse_mode=ParseMode.HTML,
                )
                return

        try:
            sent_msg = await broadcast_msg.copy(chat_id, disable_notification=silent)

            if do_pin:
                await client.pin_chat_message(chat_id, sent_msg.id, both_sides=True)
            if do_delete:
                asyncio.create_task(auto_delete(sent_msg, duration))

            successful += 1

        except FloodWait as e:
            await asyncio.sleep(e.x)
            try:
                sent_msg = await broadcast_msg.copy(chat_id, disable_notification=silent)
                if do_pin:
                    await client.pin_chat_message(chat_id, sent_msg.id, both_sides=True)
                if do_delete:
                    asyncio.create_task(auto_delete(sent_msg, duration))
                successful += 1
            except Exception:
                unsuccessful += 1

        except UserIsBlocked:
            await del_user(chat_id)
            blocked += 1

        except InputUserDeactivated:
            await del_user(chat_id)
            deleted += 1

        except Exception:
            unsuccessful += 1
            await del_user(chat_id)

        # Refresh progress bar every 5 %
        percent_complete = i / total
        if (
            percent_complete - last_update_percentage >= update_interval
            or last_update_percentage == 0
        ):
            num_blocks = int(percent_complete * bar_length)
            progress_bar = "●" * num_blocks + "○" * (bar_length - num_blocks)
            status_update = (
                f"<b>›› BROADCAST ({mode_label}) — IN PROGRESS…\n\n"
                f"<blockquote>⏳ [{progress_bar}] <code>{percent_complete:.0%}</code></blockquote>\n\n"
                f"›› Total      : <code>{total}</code>\n"
                f"›› Successful : <code>{successful}</code>\n"
                f"›› Blocked    : <code>{blocked}</code>\n"
                f"›› Deleted    : <code>{deleted}</code>\n"
                f"›› Failed     : <code>{unsuccessful}</code></b>\n\n"
                f"<i>➪ To stop, send /cancel</i>"
            )
            await pls_wait.edit(status_update, parse_mode=ParseMode.HTML)
            last_update_percentage = percent_complete

    # Final summary
    final_status = (
        f"<b>›› BROADCAST ({mode_label}) — COMPLETED ✅\n\n"
        f"<blockquote>Done: [{progress_bar}] {percent_complete:.0%}</blockquote>\n\n"
        f"›› Total      : <code>{total}</code>\n"
        f"›› Successful : <code>{successful}</code>\n"
        f"›› Blocked    : <code>{blocked}</code>\n"
        f"›› Deleted    : <code>{deleted}</code>\n"
        f"›› Failed     : <code>{unsuccessful}</code></b>"
    )
    return await pls_wait.edit(final_status, parse_mode=ParseMode.HTML)


# ==============================================================================
#  Utility — delayed message auto-delete (used by broadcast delete mode)
# ==============================================================================

async def auto_delete(sent_msg, duration: int):
    """Delete *sent_msg* after *duration* seconds."""
    await asyncio.sleep(duration)
    try:
        await sent_msg.delete()
    except Exception:
        pass


# ==============================================================================
#  Anti-spam monitor (disabled by default — remove triple-quotes to enable)
# ==============================================================================

"""
@Bot.on_message(filters.private)
async def monitor_messages(client: Bot, message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    # Ignore commands and admins
    if message.text and message.text.startswith("/"):
        return
    if user_id in ADMINS:
        return

    if user_id in user_banned_until and now < user_banned_until[user_id]:
        return await message.reply_text(
            "<b><blockquote expandable>"
            "⚠️ You have been temporarily restricted due to excessive requests.\n"
            "Please wait a while before trying again."
            "</blockquote></b>",
            parse_mode=ParseMode.HTML,
        )

    # Sliding-window rate limit
    if user_id not in user_message_count:
        user_message_count[user_id] = []

    user_message_count[user_id] = [
        t for t in user_message_count[user_id] if now - t < TIME_WINDOW
    ]
    user_message_count[user_id].append(now)

    if len(user_message_count[user_id]) > MAX_MESSAGES:
        user_banned_until[user_id] = now + BAN_DURATION
        return await message.reply_text(
            "<b><blockquote expandable>"
            "⚠️ You have been temporarily restricted due to excessive requests.\n"
            "Please wait a while before trying again."
            "</blockquote></b>",
            parse_mode=ParseMode.HTML,
        )
"""

@Bot.on_message(filters.command("help") & filters.private)
async def help_command(client: Bot, message: Message):
    await message.reply_text(HELP_MSG, parse_mode=ParseMode.HTML)