import asyncio
import time
from pyrogram import Client
from .database import (
    get_pending_messages,
    delete_messages,
    get_all_active_groups
)
from .info import API_ID, API_HASH, BOT_TOKEN

async def deletion_worker():
    """Background task to delete expired messages"""
    worker_bot = Client(
        "deletion-worker",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )

    async with worker_bot:
        print("🔄 Deletion worker started")
        while True:
            try:
                current_time = int(time.time())
                messages = get_pending_messages(current_time)
                
                if messages:
                    print(f"⏰ Processing {len(messages)} messages...")
                    success_count = 0
                    
                    for msg in messages:
                        try:
                            await worker_bot.delete_messages(
                                chat_id=msg["chat_id"],
                                message_ids=msg["message_id"]
                            )
                            success_count += 1
                        except Exception as e:
                            print(f"❌ Failed to delete {msg['message_id']}: {str(e)}")
                    
                    delete_messages(messages)
                    print(f"✅ Deleted {success_count}/{len(messages)} messages")
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"⚠️ Worker error: {str(e)}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(deletion_worker())