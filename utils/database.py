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
from info import DATABASE_URI, TIME

mongo = MongoClient(DATABASE_URI)
db = mongo.autodelete
group_collection = db.groups
messages_collection = db.messages

def authorize_group(chat_id):
    group_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"authorized": True, "time": TIME}},
        upsert=True
    )

def set_group_time(chat_id, seconds):
    group_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"time": seconds}},
        upsert=True
    )

def is_group_authorized(chat_id):
    group = group_collection.find_one({"chat_id": chat_id, "authorized": True})
    return group is not None

def get_group_time(chat_id):
    group = group_collection.find_one({"chat_id": chat_id})
    return group.get("time", TIME) if group else TIME

def save_message_for_deletion(chat_id, message_id, delete_at):
    messages_collection.insert_one({
        "chat_id": chat_id,
        "message_id": message_id,
        "delete_at": delete_at
    })

def get_expired_messages(now):
    return list(messages_collection.find({"delete_at": {"$lte": now}}))

def delete_message_record(message_id):
    messages_collection.delete_one({"_id": message_id})
