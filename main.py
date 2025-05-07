#!/usr/bin/env python3
# =========================================================================
# AutoDelete Telegram Bot - Main Application File
# Copyright (C) 2024-present
# =========================================================================

import threading
import signal
import sys
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

# Local imports
from utils.database import (
    save_message,
    get_pending_messages,
    delete_messages,
    save_group,
    get_group
)
from utils.info import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    ADMIN_ID,
    DEFAULT_TIME
)
from utils.server import run_server

# Initialize bot
Bot = Client(
    "auto-delete-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ======================== COMMAND HANDLERS ========================

async def is_admin(_, __, message: Message):
    """Check if user is admin/owner"""
    user = await Bot.get_chat_member(message.chat.id, message.from_user.id)
    return user.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

admin_filter = filters.create(is_admin)

@Bot.on_message(filters.command("start"))
async def start_command(_, message: Message):
    """Start command handler"""
    await message.reply(
        "🤖 AutoDelete Bot\n\n"
        "Available Commands:\n"
        "/auth - Enable bot in this group (Admins only)\n"
        "/settime <seconds> - Set auto-delete delay\n"
        "/status - Check bot settings"
    )

@Bot.on_message(filters.command("auth") & filters.group & admin_filter)
async def auth_group(_, message: Message):
    """Authorize group handler"""
    save_group(message.chat.id, {"active": True})
    await message.reply("✅ Bot activated for this group!")

@Bot.on_message(filters.command("settime") & filters.group & admin_filter)
async def set_delete_time(_, message: Message):
    """Set deletion time handler"""
    try:
        seconds = int(message.text.split()[1])
        if seconds < 10:
            return await message.reply("❌ Minimum time is 10 seconds")
        
        save_group(message.chat.id, {"delete_after": seconds})
        await message.reply(f"⏰ Set auto-delete to {seconds} seconds")
    except (IndexError, ValueError):
        await message.reply("⚠️ Usage: /settime <seconds>")

# ======================== MESSAGE HANDLER ========================

@Bot.on_message(filters.group)
async def handle_message(_, message: Message):
    """Main message handler"""
    group = get_group(message.chat.id)
    if not group or not group.get("active"):
        return
    
    delete_after = group.get("delete_after", DEFAULT_TIME)
    save_message(message.chat.id, message.id, int(time.time()) + delete_after)

# ======================== SHUTDOWN HANDLER ========================

def signal_handler(sig, frame):
    """Graceful shutdown handler"""
    print("\n🛑 Stopping bot gracefully...")
    sys.exit(0)

# ======================== MAIN EXECUTION ========================

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start Flask server in background thread
    flask_thread = threading.Thread(target=run_server, daemon=True)
    flask_thread.start()
    
    print("✅ Connected to MongoDB")
    print("🌐 Flask server running on port", os.getenv("PORT", 8080))
    print("🤖 Starting Telegram Bot...")
    
    # Run the bot
    Bot.run()