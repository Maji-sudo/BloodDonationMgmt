import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URI = "mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood"

async def fix():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.bloodbank

    password = "password123"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Verify it works before saving
    assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')), "Hash verification failed!"
    print(f"Hash generated & verified OK: {hashed}")

    # Update both test users
    for email in ["test@example.com", "donor@example.com"]:
        result = await db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed, "is_verified": True}}
        )
        if result.matched_count:
            print(f"Updated {email} OK")
        else:
            print(f"User {email} NOT FOUND - inserting...")
            await db.users.insert_one({
                "email": email,
                "password": hashed,
                "full_name": "Test Donor" if "donor" in email else "Test Recipient",
                "role": "donor" if "donor" in email else "recipient",
                "is_verified": True,
                "created_at": datetime.utcnow()
            })
            print(f"Inserted {email} OK")

    print("Done! Login with password: password123")

asyncio.run(fix())
