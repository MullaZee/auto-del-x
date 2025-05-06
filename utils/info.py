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

import os
from typing import List, Optional
from pymongo import MongoClient

class Config:
    # Required Telegram API credentials
    API_ID: int = int(os.getenv("API_ID", 0))
    API_HASH: str = os.getenv("API_HASH", "")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Database configuration
    DATABASE_URI: str = os.getenv("DATABASE_URI", "")
    
    # Time settings
    TIME: int = int(os.getenv("TIME", 10))  # Default deletion time in seconds
    MIN_DELETION_TIME: int = 5  # Minimum allowed seconds
    MAX_DELETION_TIME: int = 86400  # 24 hours in seconds
    
    # Access control lists
    CHATS: List[int] = [int(c) for c in os.getenv("CHATS", "").split() if c]
    WHITE_LIST: List[int] = [int(w) for w in os.getenv("WHITE_LIST", "").split() if w]
    BLACK_LIST: List[int] = [int(b) for b in os.getenv("BLACK_LIST", "").split() if b]
    ADMIN_IDS: List[int] = [int(a) for a in os.getenv("ADMIN_IDS", "").split() if a]
    
    # Server configuration
    PORT: int = int(os.getenv("PORT", 8080))
    WEBHOOK: bool = os.getenv("WEBHOOK", "false").lower() == "true"
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")

    # Database connection (will be initialized later)
    db_client: MongoClient = None
    db = None

    @classmethod
    def init_db(cls):
        """Initialize database connection"""
        if not cls.DATABASE_URI:
            raise ValueError("Database URI not configured")
        try:
            cls.db_client = MongoClient(cls.DATABASE_URI)
            cls.db = cls.db_client["AutoDeleteBot"]
            print("Database connection established")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    @classmethod
    def validate(cls):
        """Validate configuration"""
        required = {
            "API_ID": cls.API_ID,
            "API_HASH": cls.API_HASH,
            "BOT_TOKEN": cls.BOT_TOKEN,
            "DATABASE_URI": cls.DATABASE_URI
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

# Initialize when imported
Config.validate()
Config.init_db()  # This establishes the database connection