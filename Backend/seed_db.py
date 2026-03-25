import asyncio
import os
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# Simulation coordinates (Chennai area)
LOCATIONS = [
    (13.0827, 80.2707, "Chennai General Hospital"),
    (13.0067, 80.2206, "Apollo Medical Center"),
    (12.9171, 80.1923, "Global Health City"),
    (13.0405, 80.2337, "MIOT International"),
    (12.9229, 80.1275, "Tambaram Medical College")
]

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

async def seed_db():
    print("🧹 Cleaning database...")
    client = AsyncIOMotorClient("mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood")
    db = client.bloodbank
    
    await db.donors.delete_many({})
    await db.blood_requests.delete_many({})
    await db.blood_inventory.delete_many({})
    await db.users.delete_many({})

    print("🩸 Seeding Donors...")
    # Add some donors who are eligible (last donation > 3 months)
    # and some who are not
    donors = []
    for i in range(10):
        lat, lng, addr = random.choice(LOCATIONS)
        eligible_date = (datetime.now() - timedelta(days=random.randint(95, 200))).strftime("%Y-%m-%d")
        donors.append({
            "name": f"Donor {i+1}",
            "email": f"donor{i+1}@example.com",
            "phone": f"+9198765432{i}0",
            "blood_type": random.choice(BLOOD_TYPES),
            "age": random.randint(20, 50),
            "weight": float(random.randint(55, 90)),
            "last_donation_date": eligible_date,
            "lat": lat + random.uniform(-0.02, 0.02),
            "lng": lng + random.uniform(-0.02, 0.02),
            "is_available": True,
            "registered_at": datetime.utcnow()
        })
    
    # Ineligible donors (donated recently)
    for i in range(5):
        recent_date = (datetime.now() - timedelta(days=random.randint(10, 40))).strftime("%Y-%m-%d")
        donors.append({
            "name": f"Recent Donor {i+1}",
            "email": f"recent_donor{i+1}@example.com",
            "phone": f"+9191234567{i}0",
            "blood_type": random.choice(BLOOD_TYPES),
            "age": random.randint(22, 45),
            "weight": float(random.randint(60, 85)),
            "last_donation_date": recent_date,
            "lat": 13.0827,
            "lng": 80.2707,
            "is_available": True,
            "registered_at": datetime.utcnow()
        })
        
    await db.donors.insert_many(donors)

    print("🚑 Seeding Blood Requests...")
    requests = []
    # Seed a Critical Level 3 request to demonstrate prioritization
    requests.append({
        "patient_name": "Emergency Patient X",
        "email": "emergency@hospital.com",
        "phone": "+919999988888",
        "blood_type": "O+", 
        "units_needed": 4,
        "location": "Trauma Center, Teynampet",
        "lat": 13.0405, # MIOT area
        "lng": 80.2337,
        "urgency": 3,
        "is_fulfilled": False,
        "notes": "Severe accident victim. Urgent O+ needed.",
        "requested_at": datetime.utcnow() - timedelta(hours=1)
    })
    
    await db.blood_requests.insert_many(requests)

    print("📦 Seeding Inventory...")
    for b_type in BLOOD_TYPES:
        await db.blood_inventory.insert_one({
            "blood_type": b_type,
            "units": random.randint(5, 50),
            "location": "Main Blood Bank (Central)",
            "last_updated": datetime.utcnow()
        })

    print("👤 Seeding Test Users...")
    # Add a default admin/test user
    # Note: password is 'password123' hashed with bcrypt
    hashed_pwd = "$2b$12$ZpWlIDv1B9mG4X9K7V0.aeZkXf0J2FkZpG/vBf3C1R5j1iZ.fK7Oa" 
    await db.users.insert_one({
        "email": "ragulselvam006@gmail.com",
        "password": hashed_pwd,
        "full_name": "Ragul Selvam",
        "role": "admin",
        "created_at": datetime.utcnow()
    })

    print("✅ Seed complete!")

if __name__ == "__main__":
    asyncio.run(seed_db())
