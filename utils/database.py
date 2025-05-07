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

from . import * 
from pymongo import MongoClient

dbclient = MongoClient(DATABASE_URI)
db = dbclient["Auto-Delete"]
col = db["DATA"]
groups_col = db["GROUPS"]  # New collection for group settings

def save_message(message, time):
    data = {
        "chat_id": message.chat.id,
        "message_id": message.id,
        "time": time
    }
    col.insert_one(data)

def get_all_data(time):
    return list(col.find({"time": {"$lte": time}}))

def delete_all_data(all_data):
    ids = [data["_id"] for data in all_data]
    col.delete_many({"_id": {"$in": ids}})

# New functions for group settings
def save_group_settings(chat_id, auth_status=True, custom_time=None):
    groups_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"auth_status": auth_status, "custom_time": custom_time}},
        upsert=True
    )

def get_group_settings(chat_id):
    return groups_col.find_one({"chat_id": chat_id})

def get_all_authorized_groups():
    return list(groups_col.find({"auth_status": True}))