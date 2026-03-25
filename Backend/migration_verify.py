from pymongo import MongoClient
import os

uri = "mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood"
client = MongoClient(uri)
db = client['bloodbank']

# Update all users where is_verified is missing or None
result = db['users'].update_many(
    {
        "$or": [
            {"is_verified": {"$exists": False}},
            {"is_verified": None}
        ]
    },
    {"$set": {"is_verified": True}}
)

print(f"✅ UNBLOCKED USERS: {result.modified_count}")
