from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from time import time
from database import *
from info import *
import signal
import sys

# Graceful shutdown handler
def signal_handler(sig, frame):
    print("\n🛑 Stopping bot gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Initialize bot
Bot = Client(
    "auto-delete-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Admin check filter
async def is_admin(_, __, message: Message):
    user = await Bot.get_chat_member(message.chat.id, message.from_user.id)
    return user.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

admin_filter = filters.create(is_admin)

# Command handlers
@Bot.on_message(filters.command("auth") & filters.group & admin_filter)
async def enable_bot(_, message: Message):
    save_group(message.chat.id, {"active": True})
    await message.reply("✅ Bot activated for this group!")

@Bot.on_message(filters.command("settime") & filters.group & admin_filter)
async def set_time(_, message: Message):
    try:
        seconds = int(message.text.split()[1])
        if seconds < 10:
            return await message.reply("⏱ Minimum time is 10 seconds")
        
        save_group(message.chat.id, {"delete_after": seconds})
        await message.reply(f"⏰ Messages will auto-delete after {seconds} seconds")
    except (IndexError, ValueError):
        await message.reply("⚠️ Usage: /settime <seconds>")

# Message handler
@Bot.on_message(filters.group)
async def process_message(_, message: Message):
    group = get_group(message.chat.id)
    if not group or not group.get("active"):
        return
    
    delete_after = group.get("delete_after", DEFAULT_TIME)
    save_message(message.chat.id, message.id, int(time()) + delete_after)

if __name__ == "__main__":
    print("🤖 Starting AutoDelete Bot...")
    Bot.run()