#!/usr/bin/env python3
import asyncio
import logging
import signal
import sys
from time import time
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from utils.info import Config
from utils.database import (
    save_message,
    get_group_settings,
    save_group_settings,
    get_all_authorized_groups,
    get_group_deletion_time
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoDeleteBot(Client):
    def __init__(self):
        super().__init__(
            name="auto-delete-bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=100,
            sleep_threshold=10,
            in_memory=True
        )
        self._is_running = False
        self._stop_event = asyncio.Event()

    async def initialize(self):
        """Initialize the bot and load authorized groups"""
        try:
            authorized_groups = await get_all_authorized_groups()
            for group in authorized_groups:
                if group["chat_id"] not in Config.CHATS:
                    Config.CHATS.append(group["chat_id"])
            logger.info(f"Initialized {len(authorized_groups)} authorized groups")
        except Exception as e:
            logger.error(f"Error initializing chats: {e}")

    async def stop_bot(self):
        """Properly stop the bot"""
        if not self._is_running:
            logger.debug("Bot already stopped")
            return
            
        logger.info("Stopping bot...")
        try:
            if self.is_connected:
                await self.stop()
        except Exception as e:
            if "already terminated" not in str(e):
                logger.warning(f"Error during stop: {e}")
        finally:
            self._is_running = False
            self._stop_event.set()

# Initialize bot instance
bot = AutoDeleteBot()

@bot.on_message(filters.chat(Config.CHATS))
async def handle_messages(client: AutoDeleteBot, message: Message):
    try:
        settings = await get_group_settings(message.chat.id)
        if not settings or not settings.get("authorized"):
            return

        deletion_time = await get_group_deletion_time(message.chat.id) or Config.TIME

        if Config.WHITE_LIST and message.from_user.id in Config.WHITE_LIST:
            return
        if Config.BLACK_LIST and message.from_user.id not in Config.BLACK_LIST:
            return

        delete_at = int(time()) + deletion_time
        await save_message(message, delete_at)
        logger.debug(f"Scheduled deletion for message {message.id} in {message.chat.id}")

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await handle_messages(client, message)
    except Exception as e:
        logger.error(f"Error handling message in {message.chat.id}: {e}")

@bot.on_message(filters.command("start") & filters.private)
async def start(client: AutoDeleteBot, message: Message):
    help_text = """
🤖 <b>Auto-Delete Bot</b>

<b>Group Commands:</b>
• <code>!auth</code> - Authorize bot (admins only)
• <code>!unauth</code> - Remove authorization
• <code>!settime [seconds]</code> - Set custom deletion time (5-86400)
• <code>!settings</code> - View current settings

<b>Examples:</b>
• <code>!settime 60</code> - Delete after 1 minute
• <code>!settime 3600</code> - Delete after 1 hour
"""
    await message.reply(help_text, parse_mode="HTML")

async def shutdown(signal=None):
    """Clean shutdown handler"""
    if signal:
        logger.info(f"Received exit signal {signal.name}...")
    await bot.stop_bot()

async def main():
    """Main application entry point"""
    bot._is_running = True
    
    # Set up signal handlers
    loop = asyncio.get_running_loop()
    
    def handle_signal(sig):
        """Wrapper function for signal handling"""
        if not bot._stop_event.is_set():
            asyncio.create_task(shutdown(sig))
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))
        except NotImplementedError:
            logger.warning(f"Signal handling not supported for {sig}")

    try:
        await bot.initialize()
        await bot.start()
        logger.info("Bot started successfully!")
        await idle()
    except asyncio.CancelledError:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
    finally:
        if not bot._stop_event.is_set():
            await shutdown()

if __name__ == "__main__":
    try:
        Config.validate()
        
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        asyncio.run(main(), debug=True)
    except Exception as e:
        logger.critical(f"Startup failed: {e}")
        sys.exit(1)