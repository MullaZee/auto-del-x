from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import os

# Initialize MongoDB connection
try:
    client = MongoClient(os.getenv("DATABASE_URI"))
    client.admin.command('ping')  # Test connection
    db = client["AutoDelete"]
    messages_col = db["Messages"]
    groups_col = db["Groups"]
    print("✅ MongoDB connection established")
except ConnectionFailure as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)

def save_message(chat_id, message_id, delete_time):
    """Save message to database with deletion time"""
    messages_col.insert_one({
        "chat_id": chat_id,
        "message_id": message_id,
        "time": delete_time,
        "saved_at": datetime.utcnow()
    })

def get_pending_messages(current_time):
    """Get messages ready for deletion"""
    return list(messages_col.find({
        "time": {"$lte": current_time}
    }))

def delete_messages(message_list):
    """Remove processed messages from database"""
    if message_list:
        messages_col.delete_many({
            "_id": {"$in": [msg["_id"] for msg in message_list]}
        })

def save_group(chat_id, settings):
    """Save or update group settings"""
    settings["last_updated"] = datetime.utcnow()
    groups_col.update_one(
        {"chat_id": chat_id},
        {"$set": settings},
        upsert=True
    )

def get_group(chat_id):
    """Get group settings"""
    return groups_col.find_one({"chat_id": chat_id})

def get_all_active_groups():
    """List all authorized groups"""
    return list(groups_col.find({"active": True}))