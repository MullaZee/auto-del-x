#!/usr/bin/env python3
# =========================================================================
# AutoDelete Telegram Bot - All-in-One Koyeb Version
# =========================================================================

import os
import sys
import time
import signal
import asyncio
import threading
from multiprocessing import Process
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ParseMode
from flask import Flask, Response
from waitress import serve
from pymongo import MongoClient

# ==================== CONFIGURATION ====================
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URI = os.getenv("DATABASE_URI", "")
PORT = int(os.getenv("PORT", 8080))
DEFAULT_TIME = 86400  # Default: 24 hours

# Initialize MongoDB
db_client = MongoClient(DATABASE_URI)
db = db_client["AutoDelete"]
messages_col = db["Messages"]
groups_col = db["Groups"]

# ==================== FLASK SERVER ====================
def run_flask_server():
    """Run production health check server"""
    app = Flask(__name__)
    
    @app.route('/')
    def health_check():
        return Response(
            "🤖 AutoDelete Bot: ONLINE\n"
            f"🕒 {datetime.now().isoformat()}",
            status=200,
            mimetype='text/plain'
        )
    
    print(f"🌐 Health check server started on port {PORT}")
    serve(app, host="0.0.0.0", port=PORT)

# ==================== DATABASE FUNCTIONS ====================
def save_message(chat_id, message_id, delete_time):
    messages_col.insert_one({
        "chat_id": chat_id,
        "message_id": message_id,
        "time": delete_time
    })

def get_pending_messages(current_time):
    return list(messages_col.find({"time": {"$lte": current_time}}))

def delete_messages(message_list):
    ids = [msg["_id"] for msg in message_list]
    messages_col.delete_many({"_id": {"$in": ids}})

def save_group(chat_id, settings):
    groups_col.update_one(
        {"chat_id": chat_id},
        {"$set": settings},
        upsert=True
    )

def get_group(chat_id):
    return groups_col.find_one({"chat_id": chat_id})

# ==================== BOT SETUP ====================
bot = Client(
    "auto-delete-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==================== COMMAND HANDLERS ====================
async def is_admin(_, __, message: Message):
    try:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return user.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

admin_filter = filters.create(is_admin)

@bot.on_message(filters.command("start"))
async def start_command(_, message: Message):
    await message.reply(
        "🤖 <b>AutoDelete Bot</b>\n\n"
        "Commands:\n"
        "/auth - Enable in this group\n"
        "/settime [seconds] - Set deletion delay\n"
        "/status - Check settings\n"
        "/debug - Technical info",
        parse_mode=ParseMode.HTML
    )

@bot.on_message(filters.command("auth") & filters.group & admin_filter)
async def auth_group(_, message: Message):
    try:
        me = await bot.get_chat_member(message.chat.id, "me")
        if not me.privileges.can_delete_messages:
            await message.reply("❌ I need <b>Delete Messages</b> permission!", parse_mode=ParseMode.HTML)
            return
            
        save_group(message.chat.id, {
            "active": True,
            "title": message.chat.title,
            "auth_date": int(time.time())
        })
        await message.reply("✅ <b>Activated!</b> I'll delete messages here.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")

@bot.on_message(filters.command("settime") & filters.group & admin_filter)
async def set_time(_, message: Message):
    try:
        seconds = int(message.text.split()[1])
        if seconds < 10:
            await message.reply("❌ Minimum time is 10 seconds")
            return
            
        save_group(message.chat.id, {"delete_after": seconds})
        await message.reply(f"⏰ Set to delete after <b>{seconds}</b> seconds", parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await message.reply("⚠️ Usage: /settime <seconds>")

@bot.on_message(filters.command("status"))
async def show_status(_, message: Message):
    group = get_group(message.chat.id)
    if not group:
        await message.reply("❌ Bot not active in this group. Use /auth")
        return
        
    await message.reply(
        f"⚙️ <b>Status for {group.get('title', 'this group')}</b>\n\n"
        f"• Auto-delete: <b>{group.get('delete_after', DEFAULT_TIME)} seconds</b>\n"
        f"• Authorized: <b>{time.ctime(group.get('auth_date', 0))}</b>\n"
        f"• Messages in queue: <b>{messages_col.count_documents({'chat_id': message.chat.id})}</b>",
        parse_mode=ParseMode.HTML
    )

# ==================== MESSAGE PROCESSING ====================
@bot.on_message(filters.group)
async def handle_message(_, message: Message):
    try:
        group = get_group(message.chat.id)
        if not group or not group.get("active"):
            return
            
        delete_after = group.get("delete_after", DEFAULT_TIME)
        save_message(message.chat.id, message.id, int(time.time()) + delete_after)
    except Exception as e:
        print(f"Error handling message: {e}")

# ==================== DELETION WORKER ====================
async def deletion_worker():
    """Background message deletion task"""
    worker_bot = Client(
        "deletion-worker",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
    
    async with worker_bot:
        while True:
            try:
                current_time = int(time.time())
                messages = get_pending_messages(current_time)
                
                for msg in messages:
                    try:
                        await worker_bot.delete_messages(
                            chat_id=msg["chat_id"],
                            message_ids=msg["message_id"]
                        )
                    except Exception as e:
                        print(f"Delete failed for {msg['message_id']}: {e}")
                
                delete_messages(messages)
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Worker error: {e}")
                await asyncio.sleep(10)

# ==================== MAIN EXECUTION ====================
def signal_handler(signum, frame):
    print(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)

async def run_bot():
    """Start all components"""
    # Start deletion worker as background task
    asyncio.create_task(deletion_worker())
    
    # Run main bot
    await bot.start()
    print("🤖 Bot started successfully")
    await asyncio.Event().wait()  # Run forever

if __name__ == "__main__":
    # Signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start Flask in separate process
    flask_process = Process(target=run_flask_server)
    flask_process.start()
    
    # Start bot with event loop
    try:
        print("🚀 Starting all services...")
        asyncio.run(run_bot())
    finally:
        flask_process.terminate()