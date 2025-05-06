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
from typing import List, Union

class Config:
    # Required Telegram API credentials
    API_ID: int = int(os.environ.get("API_ID", ""))
    API_HASH: str = os.environ.get("API_HASH", "")
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
    
    # Session string (if needed for userbot functionality)
    SESSION: str = os.environ.get("SESSION", "")
    
    # Default deletion time (seconds)
    TIME: int = int(os.environ.get("TIME", 10))
    
    # Pre-authorized chats (legacy support)
    CHATS: List[int] = [int(cht) for cht in os.environ.get("CHATS", "").split() if cht]
    
    # Whitelist and blacklist
    WHITE_LIST: List[int] = [int(wht) for wht in os.environ.get("WHITE_LIST", "").split() if wht]
    BLACK_LIST: List[int] = [int(blk) for blk in os.environ.get("BLACK_LIST", "").split() if blk]
    
    # Database configuration
    DATABASE_URI: str = os.environ.get("DATABASE_URI", "")
    
    # Web server port
    PORT: Union[str, int] = os.environ.get("PORT", "8080")
    
    # New settings for auth system
    MIN_DELETION_TIME: int = 60  # Minimum allowed deletion time in seconds
    MAX_DELETION_TIME: int = 86400  # 24 hours in seconds
    
    # Admin controls (optional)
    ADMIN_ID: List[int] = [int(admin) for admin in os.environ.get("ADMIN_ID", "7439670062").split() if admin]
    
    # Web interface configuration (optional)
    WEBHOOK: bool = os.environ.get("WEBHOOK", "False").lower() == "true"
    WEBHOOK_URL: str = os.environ.get("WEBHOOK_URL", "")

    @classmethod
    def check_config(cls):
        """Validate essential configuration"""
        errors = []
        if not cls.API_ID:
            errors.append("API_ID is missing!")
        if not cls.API_HASH:
            errors.append("API_HASH is missing!")
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is missing!")
        if not cls.DATABASE_URI:
            errors.append("DATABASE_URI is missing!")
        
        if errors:
            raise ValueError("\n".join(errors))
        
        # Convert PORT to integer if it's numeric
        if isinstance(cls.PORT, str) and cls.PORT.isdigit():
            cls.PORT = int(cls.PORT)

# Validate configuration on import
Config.check_config()