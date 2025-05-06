#=========================================================================
# [AutoDelete - Telegram bot to delete messages after specific time]      
# Copyright (C) 2022 Arunkumar Shibu                       
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#=========================================================================

import asyncio
from time import time
from pyrogram import Client, filters
from utils import (
    API_ID, API_HASH, BOT_TOKEN, CHATS, 
    WHITE_LIST, BLACK_LIST, TIME,
    save_message, get_group_settings, save_group_settings,
    get_all_authorized_groups, get_group_deletion_time
)

# Initialize the bot
Bot = Client(
    "auto-delete-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def initialize_chats():
    """Load authorized groups into CHATS on startup"""
    authorized_groups = await get_all_authorized_groups()
    for group in authorized_groups:
        if group["chat_id"] not in CHATS:
            CHATS.append(group["chat_id"])

@Bot.on_message(filters.chat(CHATS))
async def handle_messages(bot, message):
    try:
        # Check group authorization
        settings = await get_group_settings(message.chat.id)
        if not settings or not settings.get("authorized"):
            return

        # Get custom deletion time or use default
        deletion_time = await get_group_deletion_time(message.chat.id) or TIME

        # Check white/black lists
        if WHITE_LIST and message.from_user.id in WHITE_LIST:
            return
        if BLACK_LIST and message.from_user.id not in BLACK_LIST:
            return

        # Schedule deletion
        delete_at = int(time()) + deletion_time
        await save_message(message, delete_at)

    except Exception as e:
        print(f"Error handling message: {e}")

@Bot.on_message(filters.command("start") & filters.private)
async def start(bot, message):
    help_text = (
        "🤖 Auto-Delete Bot\n\n"
        "**Group Commands:**\n"
        "`!auth` - Authorize bot in your group (admins only)\n"
        "`!unauth` - Remove authorization\n"
        "`!settime [seconds]` - Set custom deletion time (5-86400)\n"
        "`!settings` - View current settings\n\n"
        "Examples:\n"
        "`!settime 60` - Delete after 1 minute\n"
        "`!settime 3600` - Delete after 1 hour"
    )
    await message.reply(help_text)

@Bot.on_message(filters.command("auth", prefixes="!"))
async def handle_auth(bot, message):
    if message.chat.type == "private":
        return await message.reply("❌ This command works only in groups!")

    try:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in ["administrator", "creator"]:
            return await message.reply("🔒 Only admins can authorize this bot!")

        settings = await get_group_settings(message.chat.id)
        if settings and settings.get("authorized"):
            return await message.reply("ℹ️ Bot is already authorized here!")

        await save_group_settings(
            chat_id=message.chat.id,
            authorized=True,
            deletion_time=TIME  # Default time
        )
        
        if message.chat.id not in CHATS:
            CHATS.append(message.chat.id)
        
        await message.reply("✅ Bot authorized! Messages will now auto-delete.")

    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")

@Bot.on_message(filters.command("unauth", prefixes="!"))
async def handle_unauth(bot, message):
    if message.chat.type == "private":
        return await message.reply("❌ This command works only in groups!")

    try:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in ["administrator", "creator"]:
            return await message.reply("🔒 Only admins can unauthorize this bot!")

        settings = await get_group_settings(message.chat.id)
        if not settings or not settings.get("authorized"):
            return await message.reply("ℹ️ Bot wasn't authorized here!")

        await save_group_settings(
            chat_id=message.chat.id,
            authorized=False
        )
        
        if message.chat.id in CHATS:
            CHATS.remove(message.chat.id)
        
        await message.reply("❌ Bot access revoked. Messages won't be auto-deleted.")

    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")

@Bot.on_message(filters.command("settime", prefixes="!"))
async def handle_settime(bot, message):
    if message.chat.type == "private":
        return await message.reply("❌ This command works only in groups!")

    try:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in ["administrator", "creator"]:
            return await message.reply("🔒 Only admins can set deletion time!")

        # Check authorization first
        settings = await get_group_settings(message.chat.id)
        if not settings or not settings.get("authorized"):
            return await message.reply("⚠️ Please authorize bot with !auth first!")

        args = message.text.split()
        if len(args) < 2:
            return await message.reply(
                "⌛ Usage: `!settime [seconds]`\n"
                "Example: `!settime 60` for 1 minute"
            )

        try:
            seconds = int(args[1])
            if seconds < 5:
                return await message.reply("⏱ Minimum time is 5 seconds!")
            if seconds > 86400:
                return await message.reply("⏱ Maximum time is 24 hours (86400 sec)!")

            await save_group_settings(
                chat_id=message.chat.id,
                authorized=True,
                deletion_time=seconds
            )
            await message.reply(f"✅ Auto-delete time set to {seconds} seconds!")

        except ValueError:
            await message.reply("🔢 Please enter a valid number!")

    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")

@Bot.on_message(filters.command("settings", prefixes="!"))
async def handle_settings(bot, message):
    try:
        settings = await get_group_settings(message.chat.id)
        if not settings or not settings.get("authorized"):
            return await message.reply("ℹ️ Bot is not authorized in this group")

        current_time = settings.get("deletion_time", TIME)
        await message.reply(
            f"⚙️ Current Settings:\n"
            f"• Auto-delete time: {current_time} seconds\n"
            f"• Status: {'✅ Authorized' if settings.get('authorized') else '❌ Unauthorized'}"
        )
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")

async def main():
    await initialize_chats()
    await Bot.start()
    print("Bot started!")
    await idle()
    await Bot.stop()

if __name__ == "__main__":
    asyncio.run(main())