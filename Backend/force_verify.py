from pymongo import MongoClient
import os

uri = "mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood"
client = MongoClient(uri)
db = client['bloodbank']

# Force verify ALL users
result = db['users'].update_many({}, {"$set": {"is_verified": True}})

print(f"✅ SYSTEM-WIDE MIGRATION COMPLETE: Verified {result.modified_count} user accounts.")
