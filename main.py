#!/usr/bin/env python3
# =========================================================================
# AutoDelete Telegram Bot - Final Production Version
# =========================================================================

import os
import sys
import time
import signal
import threading
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ParseMode
from flask import Flask, Response
from waitress import serve

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

# ==================== FLASK HEALTH CHECK SERVER ====================
app = Flask(__name__)

@app.route('/')
def health_check():
    """Simple health check endpoint"""
    return Response("AutoDelete Bot: Running", status=200, mimetype='text/plain')

def run_flask_server():
    """Start production WSGI server"""
    print(f"🌐 Health check server running on port {PORT}")
    serve(app, host="0.0.0.0", port=PORT)

# ==================== TELEGRAM BOT SETUP ====================
bot = Client(
    "auto-delete-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==================== COMMAND HANDLERS ====================
async def is_admin(_, __, message: Message):
    """Check if user is admin/owner"""
    try:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return user.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

admin_filter = filters.create(is_admin)

@bot.on_message(filters.command("start"))
async def start_command(_, message: Message):
    """Start command with formatted help"""
    help_text = """
<b>🤖 AutoDelete Bot</b>

<u>Available Commands:</u>
• /auth - Enable bot in this group (Admins only)
• /settime [seconds] - Set auto-delete delay
• /status - Check current settings

<i>Note: Bot needs delete messages permission</i>
"""
    await message.reply(help_text, parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("auth") & filters.group & admin_filter)
async def auth_group(_, message: Message):
    """Authorize group for auto-deletion"""
    save_group(message.chat.id, {"active": True})
    await message.reply("✅ <b>Bot activated for this group!</b>", parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("settime") & filters.group & admin_filter)
async def set_delete_time(_, message: Message):
    """Set custom deletion time"""
    try:
        # Validate command format
        if len(message.text.split()) < 2:
            raise ValueError("Missing time parameter")
        
        seconds = int(message.text.split()[1])
        if seconds < 10:
            await message.reply("❌ Minimum deletion time is 10 seconds")
            return
        
        save_group(message.chat.id, {"delete_after": seconds})
        await message.reply(f"⏰ Auto-delete set to {seconds} seconds")
    except ValueError as e:
        await message.reply(f"⚠️ Invalid input: {str(e)}\nUsage: /settime [seconds]")

# ==================== MESSAGE PROCESSING ====================
@bot.on_message(filters.group)
async def process_message(_, message: Message):
    """Handle incoming group messages"""
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
    """Handle graceful shutdown"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    """Main application entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start health check server
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    print("✅ Services initialized")
    print(f"🌐 Health check endpoint: http://0.0.0.0:{PORT}")
    print("🤖 Starting Telegram Bot...")
    
    # Run the bot
    bot.run()

if __name__ == "__main__":
    main()