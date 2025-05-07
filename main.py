#!/usr/bin/env python3
# =========================================================================
# AutoDelete Telegram Bot - Production Ready Main File
# =========================================================================

import os
import sys
import time
import signal
import threading
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from flask import Flask, Response
from waitress import serve  # Production-grade WSGI server

# Local imports
from utils.database import (
    save_message,
    save_group,
    get_group
)
from utils.info import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    DEFAULT_TIME,
    PORT
)

# ==================== PRODUCTION FLASK APP ====================
app = Flask(__name__)

@app.route('/')
def health_check():
    """Simplified health check endpoint"""
    return Response("AutoDelete Bot: OK", status=200, mimetype='text/plain')

def run_flask_server():
    """Run production WSGI server"""
    print(f"🌐 Production server started on port {PORT}")
    serve(app, host="0.0.0.0", port=PORT)

# ==================== TELEGRAM BOT SETUP ====================
bot = Client(
    "auto-delete-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==================== BOT COMMAND HANDLERS ====================
async def is_admin(_, __, message: Message):
    """Check if user is admin"""
    try:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return user.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

admin_filter = filters.create(is_admin)

@bot.on_message(filters.command("start"))
async def start_command(_, message: Message):
    """Enhanced start command"""
    await message.reply(
        "🤖 <b>AutoDelete Bot</b>\n\n"
        "<u>Available Commands:</u>\n"
        "/auth - Enable bot in this group\n"
        "/settime [seconds] - Set auto-delete delay\n"
        "/status - Check current settings",
        parse_mode="HTML"
    )

@bot.on_message(filters.command("auth") & filters.group & admin_filter)
async def auth_group(_, message: Message):
    """Group authorization"""
    save_group(message.chat.id, {"active": True})
    await message.reply("✅ <b>Bot activated for this group!</b>", parse_mode="HTML")

@bot.on_message(filters.command("settime") & filters.group & admin_filter)
async def set_delete_time(_, message: Message):
    """Time configuration"""
    try:
        seconds = int(message.text.split()[1])
        if seconds < 10:
            return await message.reply("❌ Minimum time is 10 seconds")
        
        save_group(message.chat.id, {"delete_after": seconds})
        await message.reply(f"⏰ Set auto-delete to {seconds} seconds")
    except (IndexError, ValueError):
        await message.reply("⚠️ Usage: <code>/settime &lt;seconds&gt;</code>", parse_mode="HTML")

# ==================== MESSAGE PROCESSING ====================
@bot.on_message(filters.group)
async def process_message(_, message: Message):
    """Message handler with error protection"""
    try:
        group = get_group(message.chat.id)
        if not group or not group.get("active"):
            return
        
        delete_after = group.get("delete_after", DEFAULT_TIME)
        save_message(message.chat.id, message.id, int(time.time()) + delete_after)
    except Exception as e:
        print(f"⚠️ Error processing message: {e}")

# ==================== PROCESS MANAGEMENT ====================
def signal_handler(signum, frame):
    """Graceful shutdown handler"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main execution flow"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start health check server
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    print("✅ Services initialized")
    print(f"🌐 Health check: http://0.0.0.0:{PORT}")
    print("🤖 Starting Telegram Bot...")
    
    # Run bot
    bot.run()

if __name__ == "__main__":
    main()