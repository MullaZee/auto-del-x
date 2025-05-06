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

#!/usr/bin/env python3
import asyncio
import logging
from time import time
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from utils.info import Config
from utils.database import (
    save_message,
    get_group_settings,
    save_group_settings,
    get_all_authorized_groups,
    get_group_deletion_time
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the bot
Bot = Client(
    name="auto-delete-bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=100,
    sleep_threshold=10
)

async def initialize_chats():
    """Load authorized groups from database on startup"""
    try:
        authorized_groups = await get_all_authorized_groups()
        for group in authorized_groups:
            if group["chat_id"] not in Config.CHATS:
                Config.CHATS.append(group["chat_id"])
        logger.info(f"Initialized {len(authorized_groups)} authorized groups")
    except Exception as e:
        logger.error(f"Error initializing chats: {e}")

@Bot.on_message(filters.chat(Config.CHATS))
async def handle_messages(bot: Client, message: Message):
    try:
        # Check group authorization
        settings = await get_group_settings(message.chat.id)
        if not settings or not settings.get("authorized"):
            return

        # Get custom deletion time or use default
        deletion_time = await get_group_deletion_time(message.chat.id) or Config.TIME

        # Check white/black lists
        if Config.WHITE_LIST and message.from_user.id in Config.WHITE_LIST:
            return
        if Config.BLACK_LIST and message.from_user.id not in Config.BLACK_LIST:
            return

        # Schedule deletion
        delete_at = int(time()) + deletion_time
        await save_message(message, delete_at)
        logger.debug(f"Scheduled deletion for message {message.id} in {message.chat.id}")

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await handle_messages(bot, message)
    except Exception as e:
        logger.error(f"Error handling message in {message.chat.id}: {e}")

@Bot.on_message(filters.command("start") & filters.private)
async def start(bot: Client, message: Message):
    help_text = """
🤖 <b>Auto-Delete Bot</b>

<b>Group Commands:</b>
• <code>!auth</code> - Authorize bot (admins only)
• <code>!unauth</code> - Remove authorization
• <code>!settime [seconds]</code> - Set custom deletion time (5-86400)
• <code>!settings</code> - View current settings

<b>Examples:</b>
• <code>!settime 60</code> - Delete after 1 minute
• <code>!settime 3600</code> - Delete after 1 hour
"""
    await message.reply(help_text, parse_mode="HTML")

@Bot.on_message(filters.command("auth", prefixes="!"))
async def handle_auth(bot: Client, message: Message):
    try:
        if message.chat.type == "private":
            return await message.reply("❌ This command works only in groups!")

        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in ["administrator", "creator"]:
            return await message.reply("🔒 Only admins can authorize this bot!")

        settings = await get_group_settings(message.chat.id)
        if settings and settings.get("authorized"):
            return await message.reply("ℹ️ Bot is already authorized here!")

        await save_group_settings(
            chat_id=message.chat.id,
            authorized=True,
            deletion_time=Config.TIME
        )
        
        if message.chat.id not in Config.CHATS:
            Config.CHATS.append(message.chat.id)
        
        await message.reply("✅ Bot authorized! Messages will now auto-delete.")
        logger.info(f"Authorized bot in group {message.chat.id}")

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await handle_auth(bot, message)
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")
        logger.error(f"Auth error in {message.chat.id}: {e}")

@Bot.on_message(filters.command("settime", prefixes="!"))
async def handle_settime(bot: Client, message: Message):
    try:
        if message.chat.type == "private":
            return await message.reply("❌ This command works only in groups!")

        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in ["administrator", "creator"]:
            return await message.reply("🔒 Only admins can set deletion time!")

        settings = await get_group_settings(message.chat.id)
        if not settings or not settings.get("authorized"):
            return await message.reply("⚠️ Please authorize bot with !auth first!")

        args = message.text.split()
        if len(args) < 2:
            return await message.reply("⌛ Usage: <code>!settime [seconds]</code>", parse_mode="HTML")

        try:
            seconds = int(args[1])
            if seconds < Config.MIN_DELETION_TIME:
                return await message.reply(f"⏱ Minimum time is {Config.MIN_DELETION_TIME} seconds!")
            if seconds > Config.MAX_DELETION_TIME:
                return await message.reply(f"⏱ Maximum time is {Config.MAX_DELETION_TIME} seconds!")

            await save_group_settings(
                chat_id=message.chat.id,
                authorized=True,
                deletion_time=seconds
            )
            await message.reply(f"✅ Auto-delete time set to {seconds} seconds!")
            logger.info(f"Set time to {seconds}s in group {message.chat.id}")

        except ValueError:
            await message.reply("🔢 Please enter a valid number!")

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await handle_settime(bot, message)
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")
        logger.error(f"SetTime error in {message.chat.id}: {e}")

@Bot.on_message(filters.command("settings", prefixes="!"))
async def handle_settings(bot: Client, message: Message):
    try:
        settings = await get_group_settings(message.chat.id)
        if not settings or not settings.get("authorized"):
            return await message.reply("ℹ️ Bot is not authorized in this group")

        current_time = settings.get("deletion_time", Config.TIME)
        await message.reply(
            f"⚙️ <b>Current Settings:</b>\n"
            f"• Auto-delete time: <code>{current_time}</code> seconds\n"
            f"• Status: {'✅ Authorized' if settings.get('authorized') else '❌ Unauthorized'}",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")
        logger.error(f"Settings error in {message.chat.id}: {e}")

async def main():
    try:
        await initialize_chats()
        await Bot.start()
        logger.info("Bot started successfully!")
        await idle()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
    finally:
        if await Bot.stop():
            logger.info("Bot stopped gracefully")

if __name__ == "__main__":
    try:
        Config.validate()
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Startup failed: {e}")
        raise