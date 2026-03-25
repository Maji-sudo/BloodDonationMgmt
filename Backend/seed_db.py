import asyncio
from datetime import datetime
from database import connect_to_mongo, close_mongo_connection, db_instance

async def seed_data():
    await connect_to_mongo()
    db = db_instance.db
    
    # 1. Clear existing data (Optional - use with caution!)
    await db.donors.delete_many({})
    await db.blood_requests.delete_many({})
    await db.blood_inventory.delete_many({})
    print("🗑️  Cleared old data")

    # 2. Seed Donors
    donors = [
        {"name": "Alice Smith", "email": "alice@example.com", "phone": "+919888877771", "blood_type": "O+", "age": 28, "weight": 62, "is_available": True, "registered_at": datetime.utcnow()},
        {"name": "Bob Johnson", "email": "bob@example.com", "phone": "+919888877772", "blood_type": "A-", "age": 35, "weight": 75, "is_available": True, "registered_at": datetime.utcnow()},
        {"name": "Charlie Brown", "email": "charlie@example.com", "phone": "+919888877773", "blood_type": "B+", "age": 22, "weight": 58, "is_available": False, "registered_at": datetime.utcnow()},
    ]
    await db.donors.insert_many(donors)
    print(f"✅ Seeded {len(donors)} donors")

    # 3. Seed Blood Requests
    requests = [
        {
            "patient_name": "David Wilson", "email": "family@david.com", "phone": "+919000011111", 
            "blood_type": "O+", "units_needed": 2, "location": "City Hospital, Mumbai", 
            "urgency": 3, "is_fulfilled": False, "requested_at": datetime.utcnow()
        },
        {
            "patient_name": "Eve Miller", "email": "eve@sister.com", "phone": "+919000022222", 
            "blood_type": "B-", "units_needed": 1, "location": "Apollo Clinic, Pune", 
            "urgency": 2, "is_fulfilled": False, "requested_at": datetime.utcnow()
        }
    ]
    await db.blood_requests.insert_many(requests)
    print(f"✅ Seeded {len(requests)} blood requests")

    # 4. Seed Inventory
    inventory = [
        {"blood_type": "O+", "units_available": 15, "location": "Main Blood Bank, Mumbai", "last_updated": datetime.utcnow()},
        {"blood_type": "B-", "units_available": 3, "location": "Central Hub, Nagpur", "last_updated": datetime.utcnow()},
        {"blood_type": "A+", "units_available": 0, "location": "Main Blood Bank, Mumbai", "last_updated": datetime.utcnow()},
    ]
    await db.blood_inventory.insert_many(inventory)
    print(f"✅ Seeded {len(inventory)} inventory records")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(seed_data())
