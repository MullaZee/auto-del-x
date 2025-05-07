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
import logging
import time
from pyrogram import Client
from info import *
from database import get_expired_messages, delete_message_record

logging.basicConfig(level=logging.INFO)

Bot = Client("auto-delete-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def delete_expired_messages():
    while True:
        now = int(time.time())
        expired = get_expired_messages(now)
        for msg in expired:
            try:
                await Bot.delete_messages(msg["chat_id"], msg["message_id"])
                logging.info(f"Deleted message {msg['message_id']} in {msg['chat_id']}")
            except Exception as e:
                logging.warning(f"Failed to delete message {msg['message_id']]}: {e}")
            delete_message_record(msg["_id"])
        await asyncio.sleep(5)

async def main():
    await Bot.start()
    await delete_expired_messages()

if __name__ == "__main__":
    asyncio.run(main())
