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

from pyrogram import Client, filters
from pyrogram.types import Message
from time import time
from subprocess import Popen
from .database import *
from .info import *

Bot = Client(
    "auto-delete-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@Bot.on_message(filters.command("auth") & filters.group)
async def authorize_group(bot: Client, message: Message):
    chat_id = message.chat.id
    save_group_settings(chat_id, auth_status=True)
    await message.reply("✅ **Group authorized!** Messages here will now be auto-deleted.")

@Bot.on_message(filters.command("settime") & filters.group)
async def set_custom_time(bot: Client, message: Message):
    try:
        time_arg = int(message.text.split()[1])
        if time_arg < 10:
            await message.reply("❌ Time must be ≥10 seconds.")
            return
        save_group_settings(message.chat.id, custom_time=time_arg)
        await message.reply(f"⏳ **Auto-deletion time set to {time_arg} seconds.**")
    except (IndexError, ValueError):
        await message.reply("⚠️ Usage: `/settime <seconds>`")

@Bot.on_message(filters.group)
async def handle_messages(bot: Client, message: Message):
    chat_id = message.chat.id
    group = get_group_settings(chat_id)
    
    # Skip if group not authorized
    if not group or not group.get("auth_status"):
        return
    
    # Use group's custom time or default
    custom_time = group.get("custom_time", TIME)
    deletion_time = int(time()) + custom_time
    
    # Whitelist/Blacklist logic
    user_id = message.from_user.id
    if WHITE_LIST and user_id in WHITE_LIST:
        return
    if BLACK_LIST and user_id not in BLACK_LIST:
        return
    
    save_message(message, deletion_time)

@Bot.on_message(filters.command("start") & filters.private)
async def start(bot: Client, message: Message):
    await message.reply(
        "🤖 **AutoDelete Bot**\n"
        "Authorize groups with `/auth` and set time with `/settime <seconds>`"
    )

# Start server and deleter
Popen(["gunicorn", "utils.server:app", "--bind", f"0.0.0.0:{PORT}"])
Popen(["python3", "-m", "utils.delete"])
Bot.run()