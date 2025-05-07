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
import sys

# Required variables
REQUIRED_VARS = [
    "API_ID", "API_HASH", "BOT_TOKEN",
    "DATABASE_URI", "ADMIN_ID"
]

# Load environment
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URI = os.getenv("DATABASE_URI", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # Your Telegram ID
PORT = os.getenv("PORT", "8080")

# Default settings
DEFAULT_TIME = 86400  # 24 hours in seconds

# Validate configuration
missing = [var for var in REQUIRED_VARS if not globals()[var]]
if missing:
    print(f"❌ Missing environment variables: {', '.join(missing)}")
    sys.exit(1)