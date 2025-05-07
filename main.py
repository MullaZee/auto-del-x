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
from time import time
from subprocess import Popen
from pymongo import MongoClient
from pyrogram.types import Message
from info import *
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# MongoDB
mongo = MongoClient(DATABASE_URI)
db = mongo.autodelete
group_collection = db.groups
messages_collection = db.messages

Bot = Client("auto-delete-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Load authorized groups
async def get_authorized_groups():
    return [doc["chat_id"] for doc in group_collection.find({"authorized": True})]

async def get_group_time(chat_id):
    group = group_collection.find_one({"chat_id": chat_id})
    return group["time"] if group and "time" in group else TIME

async def is_admin(chat_id, user_id):
    try:
        member = await Bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

@Bot.on_message(filters.command("auth", prefixes="!") & filters.group)
async def auth_group(client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("Only admins can authorize this bot.")

    group_collection.update_one(
        {"chat_id": message.chat.id},
        {"$set": {"authorized": True, "time": TIME}},
        upsert=True
    )
    await message.reply("✅ This group has been authorized to use the bot.")

@Bot.on_message(filters.command("settime", prefixes="!") & filters.group)
async def set_custom_time(client, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("Only admins can set delete time.")

    try:
        seconds = int(message.text.split(" ")[1])
        if seconds < 5:
            return await message.reply("⛔ Minimum delete time is 5 seconds.")
    except:
        return await message.reply("Usage: !settime <seconds>")

    group_collection.update_one(
        {"chat_id": message.chat.id},
        {"$set": {"time": seconds}},
        upsert=True
    )
    await message.reply(f"✅ Message delete time set to {seconds} seconds.")

@Bot.on_message(filters.group)
async def auto_delete(client, message: Message):
    group = group_collection.find_one({"chat_id": message.chat.id, "authorized": True})
    if not group:
        return

    try:
        custom_time = group.get("time", TIME)
        delete_at = int(time()) + custom_time
        messages_collection.insert_one({
            "chat_id": message.chat.id,
            "message_id": message.id,
            "delete_at": delete_at
        })
    except Exception as e:
        logging.error("Error saving message for deletion", exc_info=True)

@Bot.on_message(filters.command("start") & filters.private)
async def start_message(client, message):
    await message.reply("Hi, I'm alive and ready to delete messages!")

# Launch background services
Popen(f"gunicorn server:app --bind 0.0.0.0:{PORT}", shell=True)
Popen("python3 delete.py", shell=True)

Bot.run()
