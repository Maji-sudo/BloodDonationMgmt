import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient("mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood")
    db = client.bloodbank
    
    email = "ragulselvam006@gmail.com"
    print(f"🔎 Checking user: {email}")
    
    user = await db.users.find_one({"email": email})
    if user:
        print(f"✅ User found! Name: {user.get('full_name')}")
    else:
        print("❌ User NOT found in the 'users' collection.")
        # Check all emails to see what's there
        print("📄 Current Users in DB:")
        async for u in db.users.find():
            print(f"- {u.get('email')}")

if __name__ == "__main__":
    asyncio.run(check())
