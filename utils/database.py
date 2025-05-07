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

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from .info import DATABASE_URI

# Initialize database with error handling
try:
    client = MongoClient(
        DATABASE_URI,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000
    )
    # Test connection
    client.admin.command('ping')
    db = client["Auto-Delete"]
    col = db["Messages"]  # Stores messages to delete
    groups_col = db["Groups"]  # Stores group settings
    print("✅ Connected to MongoDB")
except ConnectionFailure as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)

def save_message(chat_id, message_id, delete_time):
    col.insert_one({
        "chat_id": chat_id,
        "message_id": message_id,
        "time": delete_time
    })

def get_pending_messages(current_time):
    return list(col.find({"time": {"$lte": current_time}}))

def delete_messages(message_list):
    ids = [msg["_id"] for msg in message_list]
    col.delete_many({"_id": {"$in": ids}})

# Group management functions
def save_group(chat_id, settings):
    groups_col.update_one(
        {"chat_id": chat_id},
        {"$set": settings},
        upsert=True
    )

def get_group(chat_id):
    return groups_col.find_one({"chat_id": chat_id})