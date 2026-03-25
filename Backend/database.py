import os
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Default URI if not provided in environment
    MONGO_URI: str = "mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood"
    DATABASE_NAME: str = "bloodbank"

settings = Settings()

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    print("⏳ Connecting to MongoDB...")
    db_instance.client = AsyncIOMotorClient(settings.MONGO_URI)
    db_instance.db = db_instance.client[settings.DATABASE_NAME]
    
    print("⏳ Creating indexes...")
    # Create indexes for better performance
    # 1. Donors: index on blood_type and email (unique)
    await db_instance.db.donors.create_index("email", unique=True)
    await db_instance.db.donors.create_index("blood_type")
    
    # 2. Blood Requests: index on urgency and blood_type
    await db_instance.db.blood_requests.create_index([("urgency", -1), ("requested_at", 1)])
    await db_instance.db.blood_requests.create_index("blood_type")
    
    # 3. Blood Inventory: index on blood_type and location
    await db_instance.db.blood_inventory.create_index([("blood_type", 1), ("location", 1)], unique=True)
    
    # 4. Users: index on email (unique)
    await db_instance.db.users.create_index("email", unique=True)
    
    print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        print("🔌 Disconnected from MongoDB")

def get_db():
    return db_instance.db
