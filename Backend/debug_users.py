from pymongo import MongoClient
import os

uri = "mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood"
client = MongoClient(uri)
db = client['bloodbank']
users = db['users'].find()

print("LISTING USERS:")
for u in users:
    print(f"EMAIL: {u.get('email')} -> VERIFIED: {u.get('is_verified')}")
    # Also check if password reset token is clear
    print(f"  RESET TOKEN: {u.get('reset_token')}")
