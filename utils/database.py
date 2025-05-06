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

from .info import Config

# Initialize collections
messages_col = Config.db["Messages"]
groups_col = Config.db["Groups"]

def save_message(message, delete_time):
    """Save message to database for future deletion"""
    data = {
        "chat_id": message.chat.id,
        "message_id": message.id,
        "time": delete_time
    }
    messages_col.insert_one(data)

def get_all_data(current_time):
    """Get all messages scheduled for deletion"""
    query = {"time": {"$lte": current_time}}
    return list(messages_col.find(query))

def delete_all_data(data_list):
    """Delete processed messages from database"""
    for data in data_list:
        messages_col.delete_one({"_id": data["_id"]})

def save_group_settings(chat_id, authorized=False, deletion_time=None):
    """Save group settings to database"""
    settings = {
        "chat_id": chat_id,
        "authorized": authorized,
        "deletion_time": deletion_time
    }
    groups_col.update_one(
        {"chat_id": chat_id},
        {"$set": settings},
        upsert=True
    )

def get_group_settings(chat_id):
    """Get settings for specific group"""
    return groups_col.find_one({"chat_id": chat_id})

def get_all_authorized_groups():
    """Get all authorized groups"""
    return list(groups_col.find({"authorized": True}))

def get_group_deletion_time(chat_id):
    """Get custom deletion time for group"""
    settings = groups_col.find_one({"chat_id": chat_id})
    return settings.get("deletion_time") if settings else None