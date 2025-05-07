#!/usr/bin/env python3
import asyncio
import time
from pyrogram import Client
from .database import get_pending_messages, delete_messages
from .info import API_ID, API_HASH, BOT_TOKEN

bot = Client(
    "auto-delete-worker",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def delete_job():
    async with bot:
        while True:
            try:
                current_time = int(time.time())
                messages = get_pending_messages(current_time)
                
                if messages:
                    print(f"⏰ Processing {len(messages)} messages...")
                    for msg in messages:
                        try:
                            await bot.delete_messages(msg["chat_id"], msg["message_id"])
                            print(f"🗑️ Deleted message {msg['message_id']} from chat {msg['chat_id']}")
                        except Exception as e:
                            print(f"❌ Failed to delete {msg['message_id']}: {str(e)}")
                    
                    delete_messages(messages)
                
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"⚠️ Worker error: {str(e)}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    print("🔄 Starting deletion worker...")
    asyncio.run(delete_job())