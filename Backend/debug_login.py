import bcrypt
from pymongo import MongoClient

uri = "mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood"
client = MongoClient(uri)
db = client['bloodbank']
user_email = "ragulselvam006@gmail.com"
user = db['users'].find_one({"email": user_email})

if not user:
    print("USER NOT FOUND")
else:
    print(f"FOUND USER: {user['email']}")
    print(f"HASH: {user['password']}")
    print(f"VERIFIED: {user.get('is_verified')}")
    # Simulate a login attempt (if we knew their last password they tried)
